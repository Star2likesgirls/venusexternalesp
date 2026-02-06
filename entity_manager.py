# Venus External - Entity Manager
# Handles player enumeration and data reading from memory

from memory import memory
from offsets import Offsets
import math
import time

class Player:
    """Represents a player entity with all readable data"""
    def __init__(self, address=0):
        self.address = address
        self.name = ""
        self.display_name = ""
        self.user_id = 0
        self.team_color = 0
        self.position = (0.0, 0.0, 0.0)
        self.head_position = (0.0, 0.0, 0.0)
        self.health = 100.0
        self.max_health = 100.0
        self.is_local = False
        self.distance = 0.0
        self.screen_pos = None  # (x, y) on screen after w2s
        self.screen_head_pos = None
        self.humanoid_address = 0
        self.character_address = 0
        self.root_part_address = 0

class EntityManager:
    def __init__(self):
        self.players = []
        self.player_cache = {}  # Cache of Player objects keyed by address
        self.last_player_scan = 0
        self.local_player = None
        self.local_player_address = 0
        self.datamodel = 0
        self.workspace = 0
        self.players_service = 0
        self.camera = 0
        self.view_matrix = None
        self.screen_width = 1920
        self.screen_height = 1080
        self.debug = True  # Enable debug prints
        self.debug_timer = 0
        
    def debug_print(self, msg):
        """Print debug message (throttled)"""
        if self.debug and self.debug_timer <= 0:
            print(f"[ESP] {msg}")
        
    def update_base_addresses(self):
        """Get base game addresses from memory"""
        if not memory.attached:
            return False
            
        try:
            # Get DataModel from FakeDataModel
            fake_dm_ptr = memory.base_address + Offsets.fakedmptr
            fake_dm = memory.read_int64(fake_dm_ptr)
            

            
            if fake_dm == 0:
                self.debug_print(f"FakeDataModel is 0")
                return False
                
            self.datamodel = memory.read_int64(fake_dm + Offsets.fakedmtodm)
            

            
            if self.datamodel == 0:
                self.debug_print("DataModel is 0")
                return False
            
            # Get Workspace
            self.workspace = memory.read_int64(self.datamodel + Offsets.workspace)
            if self.workspace == 0:
                self.debug_print("Workspace is 0")
            
            # Get Camera
            if self.workspace:
                self.camera = memory.read_int64(self.workspace + Offsets.camera)
            
            return True
        except Exception as e:
            self.debug_print(f"Exception in update_base_addresses: {e}")
            return False
    
    def find_child(self, parent_address, name):
        """Find a child instance by name"""
        if parent_address == 0:
            return 0
            
        try:
            # Children structure uses indirection:
            # Instance + 112 -> Container pointer
            # Container + 0 = start pointer, Container + 8 = end pointer
            container = memory.read_int64(parent_address + Offsets.children)
            if container == 0:
                return 0
                
            children_start = memory.read_int64(container + 0)
            children_end = memory.read_int64(container + 8)
            
            if children_start == 0 or children_end == 0:
                return 0
            
            if children_end <= children_start:
                return 0
                
            count = (children_end - children_start) // 8
            if count > 1000 or count <= 0:
                return 0
            
            for i in range(count):
                child = memory.read_int64(children_start + i * 8)
                if child == 0:
                    continue
                    
                child_name = self.read_instance_name(child)
                if child_name == name:
                    return child
                    
            return 0
        except:
            return 0
    
    def read_instance_name(self, instance_addr):
        """Read the name of an instance using Roblox's string format"""
        if instance_addr == 0:
            return ""
        try:
            # Read the name pointer at Instance.Name offset (176)
            name_ptr = memory.read_int64(instance_addr + Offsets.name)
            if name_ptr == 0:
                return ""
            
            # Try reading as null-terminated string directly
            return memory.read_string(name_ptr, 64)
        except:
            return ""
    
    def debug_dump_children(self, parent_address, label=""):
        """Debug: dump all children names"""
        if parent_address == 0:
            print(f"[DEBUG] {label} parent is null")
            return
        
        # Children use indirection: Instance+112 -> container -> +0=start, +8=end
        container = memory.read_int64(parent_address + Offsets.children)
        if container == 0:
            print(f"[DEBUG] {label} container is 0")
            return
            
        children_start = memory.read_int64(container + 0)
        children_end = memory.read_int64(container + 8)
        
        if children_start == 0 or children_end == 0 or children_end <= children_start:
            print(f"[DEBUG] {label} invalid children pointers")
            return
            
        count = (children_end - children_start) // 8
        print(f"[DEBUG] {label} has {count} children (start: {hex(children_start)}, end: {hex(children_end)})")
        
        for i in range(min(count, 20)):  # Limit to first 20
            child = memory.read_int64(children_start + i * 8)
            if child:
                name = self.read_instance_name(child)
                print(f"[DEBUG]   Child {i}: {name} @ {hex(child)}")
    
    def get_children(self, parent_address):
        """Get all children of an instance"""
        children = []
        if parent_address == 0:
            return children
            
        try:
            # Children use indirection: Instance+112 -> container -> +0=start, +8=end
            container = memory.read_int64(parent_address + Offsets.children)
            if container == 0:
                return children
                
            children_start = memory.read_int64(container + 0)
            children_end = memory.read_int64(container + 8)
            
            if children_start == 0 or children_end == 0:
                return children
            
            if children_end <= children_start:
                return children
            
            count = (children_end - children_start) // 8
            if count > 1000 or count <= 0:
                return children
            
            for i in range(count):
                child = memory.read_int64(children_start + i * 8)
                if child != 0:
                    children.append(child)
                    
            return children
        except:
            return children
    
    def get_instance_name(self, address):
        """Get name of an instance"""
        if address == 0:
            return ""
        try:
            name_ptr = memory.read_int64(address + Offsets.name)
            if name_ptr == 0:
                return ""
            return memory.read_string(name_ptr)
        except:
            return ""
    
    def get_view_matrix(self):
        """Read the view matrix from VisualEngine"""
        if not memory.attached:
            return None
            
        try:
            visual_engine = memory.read_int64(memory.base_address + Offsets.visual_engine_base)
            if visual_engine == 0:
                self.debug_print("VisualEngine is 0")
                return None
                
            matrix_addr = visual_engine + Offsets.view_matrix_offsets[0]
            matrix = memory.read_matrix4x4(matrix_addr)
            if matrix and matrix[0] != 0:
                self.view_matrix = matrix
                return matrix
            else:
                self.debug_print(f"View matrix invalid: {matrix}")
                return None
        except Exception as e:
            self.debug_print(f"Exception reading view matrix: {e}")
            return None
    
    def world_to_screen(self, world_pos):
        """Convert world position to screen coordinates"""
        if self.view_matrix is None:
            return None
        
        # Skip zero positions
        if world_pos == (0.0, 0.0, 0.0):
            return None
            
        try:
            x, y, z = world_pos
            m = self.view_matrix
            
            # Matrix multiplication for projection (Row-Major / DirectX style)
            # vector * matrix
            clip_x = x * m[0] + y * m[1] + z * m[2] + m[3]
            clip_y = x * m[4] + y * m[5] + z * m[6] + m[7]
            clip_w = x * m[12] + y * m[13] + z * m[14] + m[15]
            
            if clip_w < 0.1:
                return None
                
            ndc_x = clip_x / clip_w
            ndc_y = clip_y / clip_w
            
            screen_x = (self.screen_width / 2) * (1 + ndc_x)
            screen_y = (self.screen_height / 2) * (1 - ndc_y)
            
            # Check if on screen
            if 0 <= screen_x <= self.screen_width and 0 <= screen_y <= self.screen_height:
                return (screen_x, screen_y)
            return None
        except:
            return None
    
    def get_part_position(self, part_address):
        """Read position from a BasePart via Primitive"""
        if part_address == 0:
            return (0.0, 0.0, 0.0)
            
        try:
            primitive = memory.read_int64(part_address + Offsets.primitive)
            if primitive == 0:
                return (0.0, 0.0, 0.0)
                
            pos = memory.read_vector3(primitive + Offsets.primitive_position)
            
            # Validate position - just check for unreasonably large values
            if any(abs(v) > 50000 for v in pos):
                return (0.0, 0.0, 0.0)
                
            return pos
        except:
            return (0.0, 0.0, 0.0)
    
    def get_class_name(self, instance_addr):
        """Get the ClassName of an instance"""
        if instance_addr == 0:
            return ""
        try:
            # ClassDescriptor is at offset 24
            class_descriptor = memory.read_int64(instance_addr + 24)
            if class_descriptor == 0:
                return ""
            # ClassName string pointer is at ClassDescriptor + 8
            name_ptr = memory.read_int64(class_descriptor + 8)
            if name_ptr:
                return self.read_instance_name_from_ptr(name_ptr)
            return ""
        except:
            return ""

    def read_instance_name_from_ptr(self, name_ptr):
        """Helper to read name from a pointer (used by both Name and ClassName)"""
        if name_ptr == 0:
            return ""
        try:
            # Try inline (short)
            raw = memory.read_bytes(name_ptr, 32)
            if raw:
                null_pos = raw.find(b'\x00')
                if null_pos > 0 and null_pos <= 16:
                    name = raw[:null_pos].decode('utf-8', errors='ignore')
                    if name.isprintable() and len(name) > 0:
                        return name
            # Try pointer (long)
            return memory.read_string(name_ptr, 64)
        except:
            return ""

    def update_players(self):
        """Update the list of all players with caching"""
        temp_players = []
        
        # Decrease debug timer
        self.debug_timer -= 1
        if self.debug_timer < 0:
            self.debug_timer = 60
        
        if not memory.attached:
            return
            
        if not self.update_base_addresses():
            return
        
        # Get view matrix
        self.get_view_matrix()
        
        # Find Players service
        if self.players_service == 0:
             self.players_service = self.find_child(self.datamodel, "Players")
        
        if self.players_service == 0:
            return

        # Get LocalPlayer address
        self.local_player_address = memory.read_int64(self.players_service + Offsets.localplayer)
        
        # --- FAST PATH: CACHE MANAGEMENT ---
        # Only scan for new/removed players once every 1.0 seconds
        current_time = time.time()
        if current_time - self.last_player_scan > 1.0:
            self.last_player_scan = current_time
            
            # Scan current player list
            current_addresses = set()
            player_instances = self.get_children(self.players_service)
            
            # Debug log periodically
            
            for addr in player_instances:
                if addr == 0: continue
                # Basic filter
                if self.get_class_name(addr) != "Player":
                    continue
                current_addresses.add(addr)
                
                # Add new players to cache
                if addr not in self.player_cache:
                    new_player = Player(addr)
                    # Read static data immediately
                    new_player.user_id = memory.read_int64(addr + Offsets.user_id)
                    new_player.name = self.read_instance_name(addr)
                    self.player_cache[addr] = new_player
            
            # Remove stale players (using list to avoid runtime change error)
            remove_keys = [k for k in self.player_cache.keys() if k not in current_addresses]
            for k in remove_keys:
                del self.player_cache[k]
                
        # --- UPDATE CACHED PLAYERS ---
        # Get local player position
        local_pos = (0.0, 0.0, 0.0)
        
        # Update all players
        for player in self.player_cache.values():
            # Update Local status
            player.is_local = (player.address == self.local_player_address)
            
            # 1. Read Character Pointer
            character = memory.read_int64(player.address + Offsets.model_instance)
            
            # 2. Check if Character changed (Respawned or first run)
            if character != player.character_address or character == 0:
                player.character_address = character
                player.root_part_address = 0
                player.humanoid_address = 0
                
                if character != 0:
                    # Scan children ONLY when character changes
                    root_part = self.find_child(character, "HumanoidRootPart")
                    if root_part == 0: # R6
                        root_part = self.find_child(character, "Torso")
                    if root_part == 0:
                        root_part = self.find_child(character, "Head")
                        
                    player.root_part_address = root_part
                    player.humanoid_address = self.find_child(character, "Humanoid")
            
            # 3. Read Dynamic Data (Position, Health) using Cached Pointers
            if player.root_part_address != 0:
                # Direct read
                player.position = self.get_part_position(player.root_part_address)
                
                # Head pos estimate
                player.head_position = (
                    player.position[0],
                    player.position[1] + 1.5,
                    player.position[2]
                )
                
                if player.is_local:
                    local_pos = player.position
            else:
                player.position = (0.0, 0.0, 0.0)
                
            if player.humanoid_address != 0:
                h = memory.read_float(player.humanoid_address + Offsets.humanoid_health)
                mh = memory.read_float(player.humanoid_address + Offsets.humanoid_max_health)
                player.health = h
                player.max_health = mh if mh > 0 else 100
                
            # 4. Projection
            if player.position != (0.0, 0.0, 0.0):
                player.screen_pos = self.world_to_screen(player.position)
                player.screen_head_pos = self.world_to_screen(player.head_position)
            else:
                player.screen_pos = None
                
            # Add to list for overlay (skip invalid name)
            if player.name and len(player.name) > 1:
                temp_players.append(player)
                
        # Update distances now that we have local pos
        if local_pos != (0.0, 0.0, 0.0):
             for p in temp_players:
                 if p.position != (0.0, 0.0, 0.0):
                    dx = p.position[0] - local_pos[0]
                    dy = p.position[1] - local_pos[1]
                    dz = p.position[2] - local_pos[2]
                    p.distance = math.sqrt(dx*dx + dy*dy + dz*dz)

        if self.local_player_address in self.player_cache:
            self.local_player = self.player_cache[self.local_player_address]
            
        # Atomic update
        self.players = temp_players

# Global entity manager
entity_manager = EntityManager()

# Venus External - Memory Reader
# Handles all memory reading operations for Roblox

import ctypes
from ctypes import wintypes
import struct

# Windows API
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
psapi = ctypes.WinDLL('psapi', use_last_error=True)

# Constants
PROCESS_ALL_ACCESS = 0x1F0FFF
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

class Memory:
    def __init__(self):
        self.process_handle = None
        self.process_id = None
        self.base_address = None
        self.attached = False
        
    def attach(self, process_name="RobloxPlayerBeta.exe"):
        """Attach to Roblox process"""
        try:
            import pymem
            self.pm = pymem.Pymem(process_name)
            self.process_handle = self.pm.process_handle
            self.process_id = self.pm.process_id
            self.base_address = self.pm.base_address
            self.attached = True
            return True
        except Exception as e:
            print(f"Failed to attach: {e}")
            self.attached = False
            return False
    
    def read_bytes(self, address, size):
        """Read raw bytes from memory"""
        if not self.attached:
            return None
        try:
            return self.pm.read_bytes(address, size)
        except:
            return None
    
    def read_int(self, address):
        """Read 4-byte integer"""
        if not self.attached:
            return 0
        try:
            return self.pm.read_int(address)
        except:
            return 0
    
    def read_uint(self, address):
        """Read 4-byte unsigned integer"""
        if not self.attached:
            return 0
        try:
            return self.pm.read_uint(address)
        except:
            return 0
    
    def read_int64(self, address):
        """Read 8-byte integer (pointer)"""
        if not self.attached:
            return 0
        try:
            return self.pm.read_longlong(address)
        except:
            return 0
    
    def read_float(self, address):
        """Read 4-byte float"""
        if not self.attached:
            return 0.0
        try:
            return self.pm.read_float(address)
        except:
            return 0.0
    
    def read_double(self, address):
        """Read 8-byte double"""
        if not self.attached:
            return 0.0
        try:
            return self.pm.read_double(address)
        except:
            return 0.0
    
    def read_string(self, address, max_length=256):
        """Read null-terminated string"""
        if not self.attached:
            return ""
        try:
            data = self.pm.read_bytes(address, max_length)
            null_pos = data.find(b'\x00')
            if null_pos != -1:
                data = data[:null_pos]
            return data.decode('utf-8', errors='ignore')
        except:
            return ""
    
    def read_roblox_string(self, address):
        """Read Roblox string (pointer to string data with length)"""
        if not self.attached:
            return ""
        try:
            # Roblox strings have length at offset 16
            str_ptr = self.read_int64(address)
            if str_ptr == 0:
                return ""
            length = self.read_int(str_ptr + 16)
            if length <= 0 or length > 256:
                return ""
            # String data follows
            return self.read_string(str_ptr, length)
        except:
            return ""
    
    def read_vector3(self, address):
        """Read Vector3 (3 floats)"""
        if not self.attached:
            return (0.0, 0.0, 0.0)
        try:
            data = self.pm.read_bytes(address, 12)
            return struct.unpack('fff', data)
        except:
            return (0.0, 0.0, 0.0)
    
    def read_matrix4x4(self, address):
        """Read 4x4 matrix (16 floats)"""
        if not self.attached:
            return None
        try:
            data = self.pm.read_bytes(address, 64)
            return struct.unpack('16f', data)
        except:
            return None
    
    def write_float(self, address, value):
        """Write 4-byte float"""
        if not self.attached:
            return False
        try:
            self.pm.write_float(address, value)
            return True
        except:
            return False
    
    def write_int(self, address, value):
        """Write 4-byte integer"""
        if not self.attached:
            return False
        try:
            self.pm.write_int(address, value)
            return True
        except:
            return False
    
    def detach(self):
        """Detach from process"""
        if self.attached:
            try:
                self.pm.close_process()
            except:
                pass
            self.attached = False
            self.process_handle = None

# Global memory instance
memory = Memory()

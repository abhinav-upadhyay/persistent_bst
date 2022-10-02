import os
from typing import BinaryIO

HEADER_OFFSET = 0
HEADER_SIZE = 128
ROOT_OFFSET = HEADER_OFFSET + HEADER_SIZE
KEY_SIZE = 64
VALUE_ADDR_SIZE = 64
NODE_ADDRESS_SIZE = 64
VALUE_LENGTH_SIZE = 4
NODE_SIZE = KEY_SIZE + 2 * NODE_ADDRESS_SIZE + VALUE_ADDR_SIZE + VALUE_LENGTH_SIZE
RECORD_SEPARATOR_BYTE = b'\n'

class BSTNode:
    def __init__(self, offset: int, index_file: BinaryIO, data_file: BinaryIO, key: int = None, value: str = None):
        self.index_file = index_file
        self.data_file = data_file
        self.value_offset: int = -1
        self.key = key
        self.value = value
        self.left_offset: int = -2
        self.right_offset: int = -2
        self.left: BSTNode = None
        self.right: BSTNode = None
        self.is_loaded = False
        self.offset = offset
        self.value_size: int = -1 if not value else len(value) + 1
        if offset == -1:
            self.index_file.seek(0, 2)
            self.offset = self.index_file.tell()
        else:
            self.offset = offset
            self.load()
    
    def __repr__(self):
        return f'key: {self.key}, value: {self.value}, left: {self.left}, right: {self.right}'
    
    def __str__(self):
        return f'key: {self.key}, value: {self.value}, left: {self.left}, right: {self.right}'
    
    def get_value(self):
        if not self.is_loaded:
            self.load()
        if self.value_offset == -1:
            return None
        self.data_file.seek(self.value_offset)
        value_bytes = self.data_file.read(self.value_size)
        self.__value = value_bytes.decode('utf-8')[:-1]
        return self.__value
    

    def load(self):
        self.index_file.seek(self.offset)
        data = self.index_file.read(NODE_SIZE)
        self.key = int.from_bytes(data[:KEY_SIZE], byteorder='big')
        self.value_size = int.from_bytes(data[KEY_SIZE:KEY_SIZE + VALUE_LENGTH_SIZE], byteorder='big')
        self.value_offset = int.from_bytes(data[KEY_SIZE + VALUE_LENGTH_SIZE:KEY_SIZE + VALUE_LENGTH_SIZE + VALUE_ADDR_SIZE], byteorder='big', signed=True)
        self.left_offset = int.from_bytes(data[KEY_SIZE + VALUE_LENGTH_SIZE + VALUE_ADDR_SIZE:KEY_SIZE + VALUE_LENGTH_SIZE + VALUE_ADDR_SIZE + NODE_ADDRESS_SIZE], byteorder='big', signed=True)
        self.right_offset = int.from_bytes(data[KEY_SIZE + VALUE_LENGTH_SIZE + VALUE_ADDR_SIZE + NODE_ADDRESS_SIZE:], byteorder='big', signed=True)
        self.is_loaded = True
        self.left = BSTNode(self.left_offset, self.index_file, self.data_file) if self.left_offset != -2 else None
        self.right = BSTNode(self.right_offset, self.index_file, self.data_file) if self.right_offset != -2 else None
    
    
    def get_key(self):
        if not self.is_loaded:
            self.load()
        return self.key
    

    def save(self, overwrite_data: bool = True):
        #TODO: exception handling required
        if overwrite_data:
            if self.value_offset == -1:
                self.data_file.seek(0, 2)
                self.value_offset = self.data_file.tell()
            if self.value:
                value_bytes = self.value.encode('utf-8') + RECORD_SEPARATOR_BYTE
                print(f'writing {value_bytes} to {self.value_offset}')
                self.data_file.seek(self.value_offset)
                self.data_file.write(value_bytes)
                self.data_file.flush()

        self.index_file.seek(self.offset)
        bytes = self.key.to_bytes(KEY_SIZE, byteorder='big') + \
                int.to_bytes(self.value_size, VALUE_LENGTH_SIZE, byteorder='big') + \
                self.value_offset.to_bytes(VALUE_ADDR_SIZE, byteorder='big', signed=True) + \
                self.left_offset.to_bytes(NODE_ADDRESS_SIZE, byteorder='big', signed=True) + \
                self.right_offset.to_bytes(NODE_ADDRESS_SIZE, byteorder='big', signed=True)
        assert len(bytes) == NODE_SIZE
        self.index_file.write(bytes)
        self.index_file.flush()
        self.is_loaded = True


class BST:
    def __init__(self):
        if not os.path.exists('index.txt'):
            open('index.txt', 'w').close()
            open('data.txt', 'w').close()
            
        self.index_file = open("index.txt", "r+b")
        self.data_file = open("data.txt", "r+b")
        self.index_file.seek(0)
        header_bytes = self.index_file.read(HEADER_SIZE)
        # we have an empty index
        if len(header_bytes) == 0:
            header = [0 for _ in range(HEADER_SIZE)]
            self.index_file.write(bytes(header))
            self.index_file.flush()
            self.root = None
        else:
            self.root = BSTNode(ROOT_OFFSET, self.index_file, self.data_file)
            self.root.load()
    
    def get(self, key: int) -> str:
        if self.root is None:
            return None
        return self._get(self.root, key)
    
    def get_all(self):
        if self.root is None:
            return []
        return self._get_all(self.root)
    
    def _get_all(self, node: BSTNode):
        if node is None:
            return []
        return self._get_all(node.left) + [(node.key, node.get_value())] + self._get_all(node.right)
    
    def _get(self, node: BSTNode, key: int) -> str:
        if node is None:
            return None
        if key < node.get_key():
            return self._get(node.left, key)
        elif key > node.get_key():
            return self._get(node.right, key)
        else:
            return node.get_value()
    
    def put(self, key: int, value: str):
        if self.root is None:
            self.root = BSTNode(-1, self.index_file, self.data_file, key=key, value=value)
            self.root.save()
            return
        
        self._put(self.root, key, value)
    
    def _put(self, node: BSTNode, key: int, value: str):
        if key < node.get_key():
            if node.left is None:
                node.left = BSTNode(-1, self.index_file, self.data_file, key=key, value=value)
                node.left.save()
                import pdb; pdb.set_trace()
                node.left_offset = node.left.offset
                node.save(overwrite_data=False)
                return
            else:
                self._put(node.left, key, value)
                return
        elif key > node.get_key():
            if node.right is None:
                node.right = BSTNode(-1, self.index_file, self.data_file, key=key, value=value)
                node.right.save()
                node.right_offset = node.right.offset
                node.save(overwrite_data=False)
                return
            else:
                self._put(node.right, key, value)
                return
        else:
            node.value = value
            node.save()
            return


if __name__ == "__main__":
    # create an interactive REPL for the BST
    print("Welcome to the BST REPL")
    bst = BST()
    while True:
        command = input("db>")
        if command == "exit" or command == "quit":
            break
        elif command.startswith("get"):
            key = command.split()[1]
            if key == "*":
                print(bst.get_all())
                continue
            print(bst.get(int(key)))
        elif command.startswith("put"):
            key, value = command.split()[1:]
            bst.put(int(key), value)
        else:
            print("Invalid command")




        
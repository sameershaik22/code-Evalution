from tree_sitter import Node 
from typing import Generator, List
from app.services.evaluation_engine import ASTParser

class ASTNormalizer:

    CONTROL_FLOW_NODES = {
        'if_statement',
        'for_statement',
        'while_statement'
    }
    ASSIGNEMENT_NODES = {
        'assignment',
        'augmented_assignment'
    }
    OPERATOR_NODES = {
        'binary_operator',
        'comparison_operator'
    }
    LITERAL_NODES = {
        'string',
        'integer',
        'float'
    }

    def __init__(self):
        self.var_map : Dict[str,str] = {}
        self.func_map : Dict[str,str] = {}
        self.var_counter = 1
        self.func_counter = 1
        self.normalized : Dict[str] = []

    def tree_normalize(self, root:Node, code:bytes) -> List[str]:
        normalized = []
        if not root:
            raise ValueError('Give a real root node')
        nodes = list(self._walk(root))
        for node in nodes:
            normalized_node = self._normalized_node(node, code)
            if normalized_node:
                normalized.append(normalized_node)

        return normalized


    def _walk(self, node:Node) -> Generator[Node, None, None]:
        if not node:
            raise ValueError("Need a proper tree node")
        yield node
        for child in node.children:
            yield from self._walk(child)
        
    def _normalized_node(self, node:Node ,code:bytes) -> str|None:
        for child in node.children:
            if child.type == 'identifier':
                name = self._get_name(child, code)
                return self._var_map(name)

            if child.type == 'function_definition':
                name = self.___get_function_name(child, code)
                return self._func_map(name)
            
            if child.type == 'call':
                return 'CALL'

            if child.type in self.CONTROL_FLOW_NODES:
                return child.type.upper()

            if child.type in self.ASSIGNEMENT_NODES:
                return 'ASSIGNMENT'

            if child.type in self.OPERATOR_NODES:
                return child.type.upper()

            if child.type in self.LITERAL_NODES:
                return 'CONSTANT'
            
            if child.type == 'return_assignment':
                return "RETURN"
            
            return None

        
    def _get_name(self, node:Node , code:bytes) -> str:
        return code[node.start_byte:node.end_byte]

    def _get_function_name(self, code:bytes, node:Node) -> str:
        node_list = node.children
        if 'name' in node_list:
            name = code[node.start_byte():node.end_byte()].decode('utf-8')
            return _func_map(name)
        
        if 'parameters' in node_list:
            return 'PARAMS'

        if 'body' in node_list:
            return "BODY"
        
    def _var_map(self, name:str) -> str:
        if name not in self.var_map:
            var_name = f'VAR_{self.var_counter}'
            self.var_counter += 1
            self.var_map[name] = var_name
        return self.var_map.get(name)

    def _func_map(self, name:str) -> str:
        if name not in self.func_map:
            func_name = f'FUNC_{self.func_counter}'
            self.func_counter += 1
            self.func_map[name] = func_name
        return self.func_map.get(name)        


































































































































































































































































































































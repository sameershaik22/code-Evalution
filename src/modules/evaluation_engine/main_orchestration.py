from src.modules import LexicalScorer, WeightedNGramScorer, Codetokenizer, ASTParser, CodeBLEU, ASTNormalizer, ASTScore
from functools import lru_cache

class EvaluationOrchestration:
    def __init__(self):
        self.tok = Codetokenizer()
        self.lex = LexicalScorer()
        self.weign = WeightedNGramScorer()
        self.ast_parser = ASTParser()
        self.cobl = CodeBLEU()
        self.normal = ASTNormalizer()
        self.ast_score = ASTScore()

    SUPPORTED_LANGS = ['python', 'java', 'javascript', 'cpp', 'c']
    MAX_LEN_OF_CODE = 10000
    def _validate_inputs(self, code:str, ref:str, language:str):
        if not code:
            raise ValueError(f"Need a valid candidate code, the old one is - {code}")
        if not ref:
            raise ValueError(f"Need a valid reference code, the old one is - {ref}")

        if len(code) > self.MAX_LEN_OF_CODE:
            raise ValueError("Candidate code is too large")

        if len(ref) > self.MAX_LEN_OF_CODE:
            raise ValueError("Reference code is too large")

        if language not in self.SUPPORTED_LANGS:
            raise ValueError('Invalid language')

        return code.strip(), ref.strip(), language.lower()


    def evaluate(self, candidate_code:str , reference_code:str, language:str) :
        candidate_code, reference_code, language = self._validate_inputs(candidate_code, reference_code, language)
        
        candidate_tokens = self.tok.tokenize(candidate_code, language = language)
        reference_tokens = self.tok.tokenize(reference_code, language = language)

        candidate_nodes = self._get_node_list(candidate_code, language)
        reference_nodes = self._get_node_list(reference_code, language)

        if not reference_tokens or not candidate_tokens:
            raise ValueError(f'There are no reference tokens or candidate tokens, maybe tokenization failed for the langauge {language}')
        
        lex_result = self.lex.score(candidate_tokens, reference_tokens)
        weign_result = self.weign.score(candidate_tokens , reference_tokens, language, n=1)
        weign_result_2 = self.weign.score(candidate_tokens, reference_tokens, language, n=2)
        weign_result_3 = self.weign.score(candidate_tokens, reference_tokens, language, n=3)
        codebl_result = self.cobl.score(candidate_code, reference_code, language)
        ast_score = self.ast_score.score(candidate_nodes, reference_nodes)

        return {
            'lexical_score' : lex_result,
            'weighted_ngram_score' : weign_result,
            "weight_2gram_score" : weign_result_2,
            "weight_3gram_score" : weign_result_3,
            "code_bleu_score" : codebl_result,
            'ast_score' : ast_score
        }

    def _get_node_list(self, code:bytes, language:str):
        tree = self.ast_parser.parse(code, language)
        root = tree.root_node
        nodes = self.normal.tree_normalize(root, code)
        return nodes
    
if __name__ == '__main__':
    candidate_code = """def compute_factorial(x):
    value = 1
    counter = 1

    while counter <= x:
        value = value * counter
        counter += 1
    
    return value

    number = 5
    print(compute_factorial(number))"""

    candidate_code_c = """
    #include <bits/stdc++.h>
    using namespace std;

    int main() {
        int n;
        cin >> n;

        int total = 0;
        int i = 1;
        while (i <= n) {
            total = total + i;
            i++;
        }

        cout << total;
        return 0;
    }

    """
    reference_code = """def factorial(n):
        if n == 0 or n == 1:
            return 1
        
        result = 1
        for i in range(2, n + 1):
            result *= i
        
        return result

        num = 5
        print(factorial(num))"""

    reference_code_c = """
    #include <iostream>
    using namespace std;

    int main() {
        int n;
        cin >> n;

        int sum = 0;
        for (int i = 1; i <= n; i++) {
            sum += i;
        }

        cout << sum << endl;
        return 0;
    }

    """

    candidate_code_java = """
    public int maxSubArrayBrute(int[] nums) {
    int max = Integer.MIN_VALUE;
    for (int i = 0; i < nums.length; i++) {
        int sum = 0;
        for (int j = i; j < nums.length; j++) {
            sum += nums[j];
            max = Math.max(max, sum);
        }
    }
    return max;
    }"""

    reference_code_java = """
    public int maxSubArray(int[] nums) {
    int maxSoFar = nums[0], currentMax = nums[0];
    for (int i = 1; i < nums.length; i++) {
        currentMax = Math.max(nums[i], currentMax + nums[i]);
        maxSoFar = Math.max(maxSoFar, currentMax);
    }
    return maxSoFar;
    }"""
    eval = EvaluationOrchestration()
    result = eval.evaluate(candidate_code_java, reference_code_java, language = 'java')
    print(result)



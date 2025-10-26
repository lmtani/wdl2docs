// WDL (Workflow Description Language) syntax highlighting for Prism.js
Prism.languages.wdl = {
    'comment': [
        {
            pattern: /#.*/,
            greedy: true
        }
    ],
    'string': {
        pattern: /(["'])(?:\\(?:\r\n|[\s\S])|(?!\1)[^\\\r\n])*\1/,
        greedy: true
    },
    'keyword': /\b(?:version|import|as|struct|workflow|task|call|command|output|runtime|meta|parameter_meta|input|if|then|else|scatter|in)\b/,
    'builtin': /\b(?:String|Int|Float|Boolean|File|Array|Map|Object|Pair)\b/,
    'boolean': /\b(?:true|false)\b/,
    'function': /\b[a-zA-Z_]\w*(?=\s*\()/,
    'number': /\b0x[\da-f]+\b|(?:\b\d+(?:\.\d*)?|\B\.\d+)(?:e[+-]?\d+)?/i,
    'operator': /[<>]=?|[!=]=?=?|--?|\+\+?|&&?|\|\|?|[?*/~^%]/,
    'punctuation': /[{}[\];(),.:]/
};

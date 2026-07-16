import sys
try:
    import openai
    print('OPENAI_VERSION', getattr(openai, '__version__', 'unknown'))
except Exception as e:
    print('OPENAI_IMPORT_ERROR', repr(e))

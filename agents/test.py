import google.generativeai as genai

# Configure your API key
genai.configure(api_key="AIzaSyBBKJANY11JGBu3aDkDFyJCotFd1ro9MP8")

# List all models available to this API key
models = genai.list_models()

for model in models:
    print(model.name, '-', model.supported_generation_methods)

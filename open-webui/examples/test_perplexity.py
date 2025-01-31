from perplexity import Pipe
import json

def test_perplexity():
    # Initialize the pipe
    pipe = Pipe()
    
    # Set the API key directly
    pipe.valves.PERPLEXITY_API_KEY = "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"
    
    # Test message
    test_body = {
        "model": "Perplexity/sonar-pro",
        "messages": [
            {"role": "user", "content": "What is the current exchange rate for EUR to PLN?"}
        ],
        "stream": True,
        "return_citations": True
    }
    
    # Test user data (can be empty for testing)
    test_user = {}
    
    try:
        # Run the pipe
        print("Sending request...")
        response = pipe.pipe(test_body, test_user)
        
        # Handle streaming response
        if test_body.get("stream", False):
            print("Streaming response:")
            try:
                for chunk in response:
                    if chunk:
                        print(chunk, end='', flush=True)
                print("\nStream completed")
            except Exception as e:
                print(f"Error in stream processing: {str(e)}")
        else:
            print("Raw response type:", type(response))
            print("Raw response:", response)
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_perplexity()
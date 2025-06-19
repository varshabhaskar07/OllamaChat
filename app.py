from flask import Flask, request, render_template_string, Response
import ollama
import markdown

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ollama Chat</title>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; }
        .container { 
            max-width: 800px; 
            margin: auto; 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
            position: relative; /* Added for positioning the icon */
        }
        h1 { text-align: center; color: #333; } 
        form { display: flex; margin-top: 20px; } 
        input[type="text"] { flex-grow: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px 0 0 4px; } 
        button { padding: 10px 15px; background-color: #007bff; color: white; border: none; border-radius: 0 4px 4px 0; cursor: pointer; } 
        button:hover { background-color: #0056b3; } 
        .response-box { background-color: #e9ecef; padding: 15px; border-radius: 4px; margin-top: 20px; white-space: pre-wrap; word-wrap: break-word; } 
        .error-message { color: red; margin-top: 10px; } 
        #response-display { margin-top: 20px; padding: 15px; background-color: #e9ecef; border-radius: 4px; } 
        
        /* Loading Spinner CSS */
        .loader {
            border: 4px solid #f3f3f3; /* Light grey */
            border-top: 4px solid #3498db; /* Blue */
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 2s linear infinite;
            display: none; /* Hidden by default */
            margin: 10px auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Chat History Icon Styling */
        .chat-history-icon {
            position: absolute;
            top: 15px; /* Adjusted for better vertical alignment */
            right: 15px; /* Adjusted for better horizontal alignment */
            font-size: 30px; /* Increased size */
            cursor: pointer;
            color: #007bff;
            z-index: 10; /* Ensure it's above other elements if needed */
        }
        .chat-history-icon:hover {
            color: #0056b3;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="chat-history-icon" title="View Chat History">&#128466;</div> <!-- Chat history icon -->
        <h1>OllamaChat :))</h1>
        <form id="chat-form">
            <input type="text" id="prompt-input" name="prompt" placeholder="Enter your prompt here..." required>
            <button type="submit">Send</button>
        </form>
        <div id="response-display"></div>
        <div id="loading-indicator" class="loader"></div> <!-- Loading indicator added here -->
        <div id="error-message" class="error-message"></div>
    </div>

    <script>
        document.getElementById('chat-form').addEventListener('submit', async function(event) {
            event.preventDefault();
            const promptInput = document.getElementById('prompt-input');
            const responseDisplay = document.getElementById('response-display');
            const loadingIndicator = document.getElementById('loading-indicator'); // Get loading indicator
            const errorMessage = document.getElementById('error-message');
            const userPrompt = promptInput.value;

            responseDisplay.innerHTML = ''; // Clear previous response
            errorMessage.textContent = ''; // Clear previous error
            promptInput.value = ''; // Clear input field

            // Display user's prompt
            responseDisplay.innerHTML += `<b>You:</b> ${userPrompt}<br><br>`;
            responseDisplay.innerHTML += `<b>Ollama:</b> <span id="ollama-response"></span>`;

            const ollamaResponseSpan = document.getElementById('ollama-response');
            let fullResponse = '';

            loadingIndicator.style.display = 'block'; // Show loading indicator

            try {
                const response = await fetch('/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `prompt=${encodeURIComponent(userPrompt)}`,
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`Server error: ${response.status} - ${errorText}`);
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    const chunk = decoder.decode(value, { stream: true });
                    fullResponse += chunk;
                    ollamaResponseSpan.innerHTML = marked.parse(fullResponse); // Render Markdown
                    responseDisplay.scrollTop = responseDisplay.scrollHeight; // Auto-scroll
                }
            } catch (e) {
                errorMessage.textContent = `Error: ${e.message}. Make sure Ollama is running and the 'llama2' model is downloaded.`;
                ollamaResponseSpan.innerHTML = ''; // Clear any partial response
            } finally {
                loadingIndicator.style.display = 'none'; // Hide loading indicator
            }
        });
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_prompt = request.form['prompt']

        def generate():
            try:
                # The default Ollama server address is http://localhost:11434
                stream = ollama.chat(model='llama2', messages=[{'role': 'user', 'content': user_prompt}], stream=True)
                for chunk in stream:
                    yield chunk['message']['content']
            except Exception as e:
                print(f"Error during Ollama chat: {e}")
                yield f"Error: Could not connect to Ollama or process request: {e}. Make sure Ollama is running and the 'llama2' model is downloaded."

        return Response(generate(), mimetype='text/plain')

    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
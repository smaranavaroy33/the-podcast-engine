This is a clear, step-by-step architectural plan to build your **Agentic AI Podcast Generator** using **Google's Agent Development Kit (ADK)** for orchestration and **Chatterbox TTS** for audio synthesis.

This plan focuses on a **Sequential Workflow**, where data flows linearly from one specialist agent to the next.

### **Phase 1: Project Initialization & Environment Setup**

Before defining agents, you need to set up the specialized environment required for both the lightweight ADK framework and the heavy-compute Chatterbox library.

1. **Create a Virtual Environment:** Isolate your project to manage conflicting dependencies between the agent framework and the audio libraries (Torch, etc.).
2. **Install ADK Framework:** Install the `google-adk` package (and the Vertex AI SDK if you are using Gemini models as the brains for your agents).
3. **Install Chatterbox:** Clone the Chatterbox repository from GitHub (`https://github.com/resemble-ai/chatterbox`). Ensure you have the necessary system libraries (like `libsndfile`) and a GPU-enabled PyTorch version if available for faster rendering.
4. **Model Configuration:** Set up your authentication for the LLM backend (e.g., Google Cloud credentials for Vertex AI) that will power the ADK agents.

---

### **Phase 2: Build the Custom Tools**

Agents in ADK need "Tools" to interact with the outside world. You need two critical tools: one for information gathering and one for audio generation.

#### **1. The Research Tool (for the Researcher Agent)**

* **Goal:** Enable the agent to fetch real-time data.
* **Implementation:** Use ADK’s built-in `Google Search` tool or wrap a custom search API (like Serper or Tavily) into an ADK `FunctionTool`.
* **Input:** A query string (e.g., "latest advancements in solid state batteries").
* **Output:** A list of search results with titles, snippets, and URLs.

#### **2. The Chatterbox Tool (for the Podcast Agent)**

* **Goal:** Enable the agent to turn the script into an audio file.
* **Implementation:** Create a custom Python function `generate_audio_segment(text, speaker_id)` and wrap it as an ADK `FunctionTool`.
* **Logic:**
* The function accepts the script text and a speaker ID (Host/Guest).
* It initializes the Chatterbox `ChatterboxTTS` model.
* It runs inference to generate a WAV file.
* It saves the file to a local `output/` directory.
* **Return:** The file path of the generated audio.



---

### **Phase 3: Define the Specialist Agents**

Using ADK’s `LlmAgent` class, you will define four distinct agents. Each requires a specific **System Instruction** (Prompt) to constrain its behavior.

#### **Agent 1: The Researcher**

* **Role:** The Fact-Finder.
* **Tools:** `Research Tool`.
* **Instructions:** "You are an expert researcher. Given a user topic, use the Search Tool to find comprehensive, accurate, and recent information. Do not summarize yet; collect raw data, statistics, and key facts from at least 3 varied sources."

#### **Agent 2: The Summarizer**

* **Role:** The Analyst.
* **Tools:** None (Pure logic).
* **Instructions:** "You are a data analyst. You will receive raw research notes. Synthesize this information into a structured summary. Highlight key themes, controversial points, and interesting facts that would make for good conversation. Ignore irrelevant metadata."

#### **Agent 3: The Scriptwriter**

* **Role:** The Creative Writer.
* **Tools:** None.
* **Instructions:** "You are a professional podcast scriptwriter. Convert the provided summary into a simplified JSON script format. Create a dialogue between two hosts: 'Host' (enthusiastic) and 'Expert' (analytical). Ensure the conversation sounds natural.
* **Format Requirement:** Output *only* a valid JSON list of objects: `[{"speaker": "Host", "text": "..."}, {"speaker": "Expert", "text": "..."}]`."



#### **Agent 4: The Podcast Producer**

* **Role:** The Audio Engineer.
* **Tools:** `Chatterbox Tool`.
* **Instructions:** "You are a podcast producer. You will receive a JSON script. Iterate through each line of the script. For every line, call the `Chatterbox Tool` with the corresponding text and speaker ID. Once all audio segments are generated, return a final success message with the location of the files."

---

### **Phase 4: Orchestrate the Workflow**

Now you must connect these agents so the output of one becomes the input of the next. In ADK, you use a **Workflow Agent**.

1. **Define a `SequentialAgent`:** This is a special ADK agent type designed to run sub-agents in a strict order.
2. **Configure the Chain:**
* **Step 1:** Pass the user's plain text topic to the **Researcher**.
* **Step 2:** Pass the Researcher's output to the **Summarizer**.
* **Step 3:** Pass the Summary to the **Scriptwriter**.
* **Step 4:** Pass the Scriptwriter's JSON output to the **Podcast Producer**.


3. **State Management:** Ensure the `SequentialAgent` is configured to pass the `last_agent_output` as the context for the next step.

---

### **Phase 5: Execution & Output Handling**

1. **Initialize the Run:** Create a `main.py` entry point. Instantiate the `SequentialAgent` (the manager) and call its `.invoke()` method with the user's prompt (e.g., "The rise of AI Agents").
2. **Post-Processing (Optional):** The Podcast Agent will generate individual audio clips (e.g., `line_1.wav`, `line_2.wav`). You may want to add a small Python utility *outside* the agent workflow (using `ffmpeg` or `pydub`) to stitch these clips into a single `final_podcast.wav` file with background music.

### **Phase 6: User Interface (Streamlit)**
This final phase adds a frontend to the agentic workflow. The UI will allow users to input a topic, visualize the agents' "thinking process" (Research -> Summary -> Script), and finally listen to the generated podcast directly in the browser.
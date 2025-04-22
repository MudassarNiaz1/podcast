
import ast, re, os, nest_asyncio, asyncio, shutil
from gtts import gTTS
import edge_tts
import ffmpeg
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import (
        SystemMessage,
        HumanMessage,
    )
from dotenv import load_dotenv
def generate_podcast(text):
    # Load environment variables and check for OPENAI_API_KEY
    load_dotenv()
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
    
    nest_asyncio.apply()

    # Initialize OpenAI (OpenRouter) client
    client = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001")

    # Prompt for dialogue generation
    SYSTEM_PROMPT = """
    You are an international Oscar-winning screenwriter.

    You have been working with multiple award-winning podcasters.

    Your job is to use the podcast transcript written below to re-write it for an AI Text-To-Speech Pipeline. A very dumb AI had written this so you have to step up for your kind.

    Make it as engaging as possible, Speaker 1 and 2 will be simulated by different voice engines.

    Speaker 1: Leads the conversation, asking insightful and thought-provoking questions. Speaker 1 digs deep into the topic, often bringing up real-world examples, analogies, and anecdotes to make the conversation more relatable and interesting. Speaker 1 keeps the conversation flowing and encourages Speaker 2 to elaborate, making sure the podcast is informative and entertaining.

    Speaker 2: Answers Speaker 1’s questions and provides in-depth responses. Speaker 2 is curious, open to new ideas, and engages in the conversation with enthusiasm. Their responses include personal experiences, analogies, and thoughtful reflections, ensuring the discussion is rich and engaging.

    The tone should be conversational, with a good balance between informative and entertaining content.

    Strictly format your response as a list of tuples, where each tuple contains the speaker’s name and the dialogue.

    Respond ONLY with a Python list of tuples formatted like: [("Speaker 1", "text"), ("Speaker 2", "text"), ...]
    No additional text or explanations.

    START YOUR RESPONSE DIRECTLY WITH THE LIST:
    """

    # Generate the podcast script from the cleaned text
    try:

        response = client.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=text)
            ]
        )
        raw_output = response.content.strip()
    except Exception as e:
        raise ValueError(f"Error during OpenAI API call: {str(e)}")

    # Save LLM raw response to file
    with open("llm_raw_output.txt", "w", encoding="utf-8") as debug_file:
        debug_file.write(raw_output)

    # Attempt to extract and evaluate the dialogue
    try:
        dialogue = ast.literal_eval(raw_output)
    except Exception:
        match = re.search(r"\[\s*\(.*?\)\s*\]", raw_output, re.DOTALL)
        if match:
            try:
                dialogue = ast.literal_eval(match.group(0))
            except Exception as inner_e:
                raise ValueError(f"Matched content found but failed to evaluate: {inner_e}")
        else:
            raise ValueError("Could not extract dialogue list from AI response. Check llm_raw_output.txt")

    # Separate speaker lines
    os.makedirs("audio", exist_ok=True)
    speaker_1_lines = [line for speaker, line in dialogue if speaker == "Speaker 1"]
    speaker_2_lines = [line for speaker, line in dialogue if speaker == "Speaker 2"]

    # Async voice generator for Speaker 2
    async def generate_edge_voice(text, filename, voice="en-GB-RyanNeural"):
        communicate = edge_tts.Communicate(text, voice=voice)
        await communicate.save(filename)

    num_lines = min(len(speaker_1_lines), len(speaker_2_lines))

    # Generate Speaker 1 audio clips synchronously (gTTS)
    for i in range(num_lines):
        speaker1_path = f"audio/speaker1_{i}.mp3"
        gTTS(speaker_1_lines[i], lang='en', tld='com').save(speaker1_path)

    # Async function to generate all Speaker 2 voices in parallel
    async def generate_all_voices():
        tasks = []
        for i in range(num_lines):
            speaker2_path = f"audio/speaker2_{i}.mp3"
            tasks.append(generate_edge_voice(speaker_2_lines[i], speaker2_path))
        await asyncio.gather(*tasks)

    # Run the async generation once
    asyncio.run(generate_all_voices())

    # After generating all audio files, create segment list for concatenation
    segment_list = []
    for i in range(num_lines):
        speaker1_path = f"audio/speaker1_{i}.mp3"
        speaker2_path = f"audio/speaker2_{i}.mp3"
        segment_list.extend([
            f"file '{os.path.abspath(speaker1_path)}'",
            f"file '{os.path.abspath(speaker2_path)}'"
        ])

    # Write list for FFmpeg
    concat_file_path = "audio/inputs.txt"
    with open(concat_file_path, "w", encoding="utf-8") as f:
        for line in segment_list:
            f.write(line + "\n")

    # Generate final podcast file
    final_audio_path = "audio/podcast_episode.mp3"
    ffmpeg.input(concat_file_path, format='concat', safe=0).output(final_audio_path, acodec='copy').overwrite_output().run()

    # Move to static folder (ensure old file is removed if exists)
    static_path = os.path.join("static", "generated_podcast.mp3")
    os.makedirs("static", exist_ok=True)

    if os.path.exists(static_path):
        os.remove(static_path)

    shutil.move(final_audio_path, static_path)

    return static_path

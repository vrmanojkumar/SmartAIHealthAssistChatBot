import random
import pandas as pd
import streamlit as st
import os
from sentence_transformers import SentenceTransformer, util
from googletrans import Translator
import gtts
from io import BytesIO
import base64

# Page configuration
st.set_page_config(
    page_title="AI Health Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .response-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .voice-button {
        background-color: #4CAF50;
        color: white;
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-size: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Load your data
@st.cache_data
def load_data():
    # Try multiple paths to find the dataset
    possible_paths = [
        'dataset - Sheet1.csv',  # Current directory
        os.path.join(os.path.dirname(__file__), 'dataset - Sheet1.csv'),  # Script directory
        os.path.join(os.getcwd(), 'dataset - Sheet1.csv'),  # Working directory
        os.path.join(os.getcwd(), 'AI-Health-Assistant-main', 'dataset - Sheet1.csv'),  # Subdirectory
    ]
    
    for csv_path in possible_paths:
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                if len(df) > 0:
                    return df
                else:
                    st.error(f"Dataset file {csv_path} is empty.")
                    continue
            except Exception as e:
                continue
    
    # If no file found, show error
    st.error("❌ Dataset file 'dataset - Sheet1.csv' not found. Please ensure the file exists in the project directory.")
    st.stop()
    return None

try:
    df = load_data()
except Exception as e:
    st.error(f"Failed to load dataset: {str(e)}")
    st.stop()
    df = None

# Initialize the SentenceTransformer model
@st.cache_resource
def load_model():
    try:
        with st.spinner("🔄 Loading AI model (this may take a moment on first run)..."):
            model = SentenceTransformer('all-MiniLM-L6-v2')
        return model
    except Exception as e:
        st.error(f"❌ Failed to load AI model: {str(e)}")
        st.error("Please ensure you have an internet connection for the first run to download the model.")
        st.stop()
        return None

try:
    model = load_model()
    if model is None:
        st.stop()
except Exception as e:
    st.error(f"Error initializing model: {str(e)}")
    st.stop()
    model = None

# Enhanced medical keywords with detailed responses
medical_keywords = {
    "fever": """Based on your symptoms, you may be experiencing a fever. Here's a comprehensive guide:

**Immediate Steps:**
- Stay hydrated by drinking plenty of water, herbal teas, or electrolyte solutions
- Rest adequately to help your body fight the infection
- Monitor your temperature regularly
- Use a cool compress on your forehead or take a lukewarm bath

**Medications:**
- Over-the-counter fever reducers like acetaminophen (paracetamol) or ibuprofen can help
- Follow dosage instructions carefully
- Avoid aspirin in children and teenagers

**When to Seek Medical Attention:**
- If fever persists for more than 3 days
- If temperature exceeds 103°F (39.4°C)
- If accompanied by severe headache, rash, or difficulty breathing
- If you experience confusion or seizures

**Prevention:**
- Practice good hygiene
- Get vaccinated as recommended
- Maintain a healthy lifestyle to boost immunity

Remember, this is general advice. For persistent or severe symptoms, please consult a healthcare professional immediately.""",

    "cough": """A persistent cough can be concerning. Here's detailed information:

**Types of Cough:**
- Dry cough: Often caused by allergies, asthma, or viral infections
- Productive cough: May indicate bacterial infection or bronchitis

**Home Remedies:**
- Drink warm fluids like honey-lemon tea, ginger tea, or warm water
- Use a humidifier to add moisture to the air
- Gargle with warm salt water
- Avoid irritants like smoke, dust, and strong perfumes
- Elevate your head while sleeping

**Medications:**
- Cough suppressants for dry coughs
- Expectorants for productive coughs
- Antihistamines if allergies are the cause
- Antibiotics only if bacterial infection is confirmed

**When to See a Doctor:**
- If cough lasts more than 3 weeks
- If accompanied by chest pain, shortness of breath, or blood
- If you have a high fever
- If cough disrupts sleep significantly

**Prevention:**
- Avoid smoking and secondhand smoke
- Stay away from allergens
- Practice good hand hygiene
- Get flu and pneumonia vaccinations

Consult a healthcare provider if symptoms worsen or persist.""",

    "headache": """Headaches can have various causes. Here's comprehensive guidance:

**Common Types:**
- Tension headaches: Most common, often stress-related
- Migraines: Severe, often with nausea and sensitivity to light
- Cluster headaches: Intense pain around one eye
- Sinus headaches: Related to sinus congestion

**Immediate Relief:**
- Rest in a quiet, dark room
- Apply cold or warm compress to forehead or neck
- Stay hydrated
- Practice relaxation techniques or deep breathing
- Gentle neck and shoulder stretches

**Medications:**
- Over-the-counter pain relievers (acetaminophen, ibuprofen, aspirin)
- For migraines: Triptans may be prescribed
- Avoid overuse to prevent medication-overuse headaches

**Lifestyle Changes:**
- Maintain regular sleep schedule
- Eat regular meals to avoid low blood sugar
- Manage stress through meditation, yoga, or exercise
- Limit alcohol and caffeine intake
- Stay hydrated throughout the day

**When to Seek Emergency Care:**
- Sudden, severe headache (thunderclap headache)
- Headache after head injury
- Headache with fever, stiff neck, or confusion
- Headache with vision changes or weakness

**Prevention:**
- Identify and avoid triggers
- Regular exercise
- Adequate sleep
- Stress management techniques

If headaches are frequent or severe, consult a healthcare professional for proper diagnosis and treatment.""",

    "cold": """Common colds are usually self-limiting. Here's detailed guidance:

**Symptoms:**
- Runny or stuffy nose
- Sneezing
- Sore throat
- Cough
- Mild body aches
- Low-grade fever

**Treatment:**
- Rest: Allow your body time to recover
- Hydration: Drink plenty of fluids (water, herbal teas, warm soups)
- Steam inhalation: Helps clear nasal passages
- Saline nasal sprays: Can relieve congestion
- Gargling: Warm salt water for sore throat
- Honey: Can soothe cough (not for children under 1 year)

**Medications:**
- Decongestants: For nasal congestion
- Pain relievers: For body aches and fever
- Cough suppressants: If cough is disruptive
- Antihistamines: May help with runny nose

**Home Remedies:**
- Chicken soup: Provides hydration and nutrients
- Vitamin C: May help reduce duration (though evidence is mixed)
- Zinc lozenges: May shorten cold duration if taken early
- Echinacea: Some studies suggest it may help

**Prevention:**
- Frequent handwashing
- Avoid touching face with unwashed hands
- Stay away from sick individuals
- Disinfect frequently touched surfaces
- Maintain a healthy lifestyle to boost immunity

**When to See a Doctor:**
- Symptoms last more than 10 days
- High fever (above 101.3°F)
- Severe symptoms or difficulty breathing
- Symptoms that improve then worsen

Most colds resolve within 7-10 days. If symptoms persist or worsen, consult a healthcare provider."""
}

# Enhanced health tips with detailed information
health_tips = {
    "sleep": [
        """**Comprehensive Sleep Guide:**

**Recommended Sleep Duration:**
- Adults (18-64 years): 7-9 hours per night
- Older adults (65+): 7-8 hours per night
- Teenagers: 8-10 hours per night

**Benefits of Quality Sleep:**
- Improves memory and cognitive function
- Strengthens immune system
- Regulates mood and reduces stress
- Supports physical recovery and growth
- Maintains healthy weight

**Tips for Better Sleep:**
- Establish a consistent sleep schedule (even on weekends)
- Create a relaxing bedtime routine (reading, meditation, warm bath)
- Make your bedroom comfortable (cool temperature, dark, quiet)
- Avoid screens 1-2 hours before bed (blue light disrupts sleep)
- Limit caffeine and alcohol, especially in the evening
- Exercise regularly but not too close to bedtime
- Avoid large meals before sleep

**Sleep Hygiene Practices:**
- Use your bed only for sleep and intimacy
- If you can't sleep, get up and do something relaxing
- Keep a sleep diary to track patterns
- Consider relaxation techniques like deep breathing or progressive muscle relaxation

**When to Consult a Doctor:**
- Persistent insomnia
- Excessive daytime sleepiness
- Loud snoring or breathing interruptions
- Restless legs syndrome

Prioritize sleep as an essential component of your health and well-being.""",

        """**Sleep Routine Optimization:**

**Creating a Sleep Schedule:**
- Go to bed and wake up at the same time daily
- Gradually adjust your schedule if needed (15-minute increments)
- Be patient - it takes time to establish new patterns

**Pre-Sleep Activities:**
- Dim lights 1 hour before bed
- Practice gentle stretching or yoga
- Listen to calming music or nature sounds
- Write in a journal to clear your mind
- Practice gratitude or meditation

**Bedroom Environment:**
- Optimal temperature: 65-68°F (18-20°C)
- Use blackout curtains or eye mask
- Consider white noise machine or earplugs
- Ensure comfortable mattress and pillows
- Keep room clean and clutter-free

**Foods That Help Sleep:**
- Cherries (natural melatonin)
- Almonds (magnesium)
- Warm milk (tryptophan)
- Chamomile tea
- Bananas (potassium and magnesium)

**Foods to Avoid Before Bed:**
- Caffeine (coffee, tea, chocolate)
- Alcohol (disrupts sleep cycles)
- Heavy, spicy, or fatty foods
- High-sugar foods

**Technology and Sleep:**
- Use blue light filters on devices
- Set "Do Not Disturb" mode
- Charge devices away from bed
- Consider using apps for sleep tracking

Remember, quality sleep is crucial for physical and mental health. Make it a priority!"""
    ],
    "energy": [
        """**Comprehensive Energy Boost Guide:**

**Nutrition for Energy:**
- Eat balanced meals with complex carbohydrates, proteins, and healthy fats
- Include iron-rich foods (leafy greens, lean meats, beans)
- Stay hydrated (dehydration causes fatigue)
- Eat regular meals to maintain blood sugar levels
- Include B-vitamin rich foods (whole grains, eggs, dairy)

**Foods That Boost Energy:**
- Oatmeal (slow-release carbohydrates)
- Nuts and seeds (healthy fats and protein)
- Leafy green vegetables (iron and B-vitamins)
- Lean proteins (chicken, fish, tofu)
- Fruits (natural sugars and vitamins)
- Dark chocolate (in moderation, contains caffeine and antioxidants)

**Exercise for Energy:**
- Regular physical activity increases energy levels
- Start with 10-15 minutes daily, gradually increase
- Mix cardio, strength training, and flexibility exercises
- Morning exercise can boost energy throughout the day
- Even a 10-minute walk can help

**Hydration:**
- Drink 8-10 glasses of water daily
- Dehydration is a common cause of fatigue
- Include electrolyte-rich drinks if needed
- Limit caffeinated beverages (they can cause crashes)

**Sleep and Energy:**
- Ensure 7-9 hours of quality sleep
- Maintain consistent sleep schedule
- Address sleep disorders if present

**Stress Management:**
- Chronic stress drains energy
- Practice relaxation techniques
- Take regular breaks throughout the day
- Learn to say no to avoid overcommitment

**Medical Considerations:**
- Check for underlying conditions (anemia, thyroid issues, diabetes)
- Regular health check-ups
- Consider vitamin D and B12 supplements if deficient

**Quick Energy Boosters:**
- Take a 10-minute power nap
- Step outside for fresh air and sunlight
- Do a few stretches or light exercises
- Listen to upbeat music
- Socialize with positive people

If fatigue persists despite lifestyle changes, consult a healthcare professional.""",

        """**Sustained Energy Management:**

**Understanding Energy Cycles:**
- Most people have natural energy peaks and dips
- Identify your peak hours and schedule important tasks then
- Plan rest periods during low-energy times

**Meal Timing:**
- Eat breakfast within 1 hour of waking
- Have small, frequent meals instead of large ones
- Include protein in every meal
- Avoid skipping meals

**Supplements That May Help:**
- B-complex vitamins
- Iron (if deficient)
- Vitamin D
- Magnesium
- Coenzyme Q10

**Lifestyle Habits:**
- Limit alcohol consumption
- Quit smoking
- Manage stress effectively
- Maintain healthy weight
- Stay socially active

**Mental Energy:**
- Take mental breaks during work
- Practice mindfulness
- Engage in hobbies
- Learn new skills
- Avoid multitasking

**Environmental Factors:**
- Ensure good lighting (natural light preferred)
- Maintain comfortable temperature
- Reduce noise distractions
- Organize your workspace

**Warning Signs:**
- Persistent fatigue despite adequate rest
- Unexplained weight changes
- Mood changes
- Difficulty concentrating
- Physical symptoms (pain, weakness)

If you experience persistent low energy, it's important to consult with a healthcare provider to rule out medical conditions."""
    ],
    "stress": [
        """**Comprehensive Stress Management Guide:**

**Understanding Stress:**
- Stress is your body's response to challenges or demands
- Acute stress can be helpful (fight-or-flight response)
- Chronic stress can harm physical and mental health

**Physical Symptoms of Stress:**
- Headaches or muscle tension
- Fatigue or sleep problems
- Digestive issues
- Rapid heartbeat or chest pain
- Weakened immune system

**Emotional Symptoms:**
- Anxiety or worry
- Irritability or anger
- Depression or sadness
- Feeling overwhelmed
- Difficulty concentrating

**Stress Management Techniques:**

**1. Breathing Exercises:**
- Deep breathing: Inhale for 4 counts, hold for 4, exhale for 4
- Box breathing: 4-4-4-4 pattern
- Practice regularly, especially during stressful moments

**2. Physical Activity:**
- Regular exercise releases endorphins (natural mood boosters)
- Aim for 30 minutes most days
- Activities: walking, jogging, yoga, dancing, swimming
- Even 10 minutes can help

**3. Mindfulness and Meditation:**
- Practice daily meditation (start with 5-10 minutes)
- Mindfulness: focus on present moment without judgment
- Use apps or guided meditations
- Progressive muscle relaxation

**4. Time Management:**
- Prioritize tasks (urgent vs. important)
- Break large tasks into smaller steps
- Learn to say no
- Delegate when possible
- Avoid overcommitment

**5. Social Support:**
- Talk to friends, family, or support groups
- Don't isolate yourself
- Seek professional help if needed
- Build strong relationships

**6. Healthy Lifestyle:**
- Maintain regular sleep schedule
- Eat balanced, nutritious meals
- Limit caffeine and alcohol
- Avoid smoking and drugs

**7. Relaxation Activities:**
- Reading
- Listening to music
- Gardening
- Hobbies
- Spending time in nature
- Taking warm baths

**When to Seek Professional Help:**
- Stress interferes with daily life
- Thoughts of self-harm
- Substance abuse
- Persistent anxiety or depression
- Physical symptoms worsen

**Prevention:**
- Regular exercise
- Healthy diet
- Adequate sleep
- Strong social connections
- Realistic expectations
- Regular breaks and vacations

Remember, managing stress is essential for overall health and well-being.""",

        """**Advanced Stress Reduction Strategies:**

**Cognitive Techniques:**
- Reframe negative thoughts
- Practice positive self-talk
- Challenge irrational beliefs
- Focus on what you can control
- Accept what you cannot change

**Professional Therapies:**
- Cognitive Behavioral Therapy (CBT)
- Biofeedback
- Counseling or psychotherapy
- Stress management programs

**Workplace Stress:**
- Set boundaries between work and personal life
- Take regular breaks
- Communicate concerns with supervisors
- Organize workspace
- Learn to delegate

**Financial Stress:**
- Create a budget
- Seek financial counseling if needed
- Focus on needs vs. wants
- Plan for emergencies
- Avoid unnecessary debt

**Relationship Stress:**
- Communicate openly and honestly
- Set healthy boundaries
- Seek couples or family therapy if needed
- Practice empathy and understanding
- Resolve conflicts constructively

**Self-Care Practices:**
- Schedule regular "me time"
- Practice gratitude daily
- Keep a journal
- Set realistic goals
- Celebrate small achievements

**Warning Signs of Excessive Stress:**
- Frequent illness
- Changes in appetite
- Sleep disturbances
- Mood swings
- Difficulty making decisions
- Withdrawal from activities

**Emergency Stress Relief:**
- Count to 10 before reacting
- Take a walk
- Practice deep breathing
- Listen to calming music
- Visualize a peaceful place

If stress becomes unmanageable, don't hesitate to seek professional help. Your mental health is as important as your physical health."""
    ],
    "general": [
        """**Comprehensive Health and Wellness Guide:**

**Hydration:**
- Drink 8-10 glasses of water daily (more if active or in hot weather)
- Water helps: regulate body temperature, transport nutrients, flush toxins, maintain organ function
- Signs of dehydration: dark urine, dry mouth, fatigue, dizziness
- Include water-rich foods: cucumbers, watermelon, oranges, tomatoes
- Limit sugary drinks and excessive caffeine

**Exercise:**
- Aim for at least 150 minutes of moderate-intensity exercise per week
- Include: cardio (walking, running, cycling), strength training (2-3 times/week), flexibility (stretching, yoga)
- Benefits: improves heart health, strengthens bones, boosts mood, helps weight management, improves sleep
- Start slowly if new to exercise
- Find activities you enjoy to maintain consistency
- Even 10-minute sessions throughout the day count

**Nutrition:**
- Eat a variety of foods from all food groups
- Include: fruits (2-3 servings), vegetables (3-5 servings), whole grains, lean proteins, healthy fats
- Limit: processed foods, added sugars, saturated fats, sodium
- Practice portion control
- Eat mindfully (pay attention to hunger cues)
- Plan meals ahead to make healthy choices easier

**Preventive Care:**
- Regular health check-ups and screenings
- Vaccinations as recommended
- Dental check-ups twice yearly
- Eye exams regularly
- Know your family medical history

**Mental Health:**
- Practice stress management
- Maintain social connections
- Get adequate sleep
- Seek help when needed
- Practice gratitude and positive thinking

**Healthy Habits:**
- Don't smoke or use tobacco
- Limit alcohol consumption
- Practice good hygiene
- Protect skin from sun damage
- Maintain healthy weight

Small, consistent changes lead to significant health improvements over time!""",

        """**Daily Health Maintenance:**

**Morning Routine:**
- Start with a glass of water
- Eat a nutritious breakfast
- Get some sunlight (vitamin D)
- Practice gratitude or meditation
- Do light stretching or exercise

**Throughout the Day:**
- Stay hydrated
- Take breaks from screens
- Move every hour (desk workers)
- Eat regular, balanced meals
- Practice good posture

**Evening Routine:**
- Wind down 1-2 hours before bed
- Avoid heavy meals late
- Limit screen time
- Practice relaxation
- Prepare for next day

**Weekly Goals:**
- 150+ minutes of exercise
- 7-9 hours sleep nightly
- Social connection
- Meal planning
- Self-care activities

**Monthly Goals:**
- Health check-ups as needed
- Review and adjust goals
- Try new healthy recipes
- Explore new activities
- Assess progress

**Building Healthy Habits:**
- Start with one change at a time
- Make it specific and measurable
- Set realistic goals
- Track progress
- Reward yourself
- Be patient and persistent

**Common Barriers:**
- Lack of time: Start with 5-10 minutes
- Lack of motivation: Find an accountability partner
- Cost: Many free resources available
- Perfectionism: Progress over perfection

Remember, health is a journey, not a destination. Every small step counts!"""
    ]
}

# Function to get personalized health tip with detailed response
def get_personalized_health_tip(user_input):
    user_input_lower = user_input.lower()
    
    if "tired" in user_input_lower or "fatigue" in user_input_lower or "exhausted" in user_input_lower:
        return random.choice(health_tips["energy"])
    elif "sleep" in user_input_lower or "rest" in user_input_lower or "insomnia" in user_input_lower:
        return random.choice(health_tips["sleep"])
    elif "stress" in user_input_lower or "anxious" in user_input_lower or "worried" in user_input_lower or "pressure" in user_input_lower:
        return random.choice(health_tips["stress"])
    else:
        return random.choice(health_tips["general"])

# Enhanced function to find the best cure with detailed response
def find_best_cure(user_input):
    # Safety checks
    if model is None:
        return "❌ AI model is not loaded. Please refresh the page."
    if df is None or len(df) == 0:
        return "❌ Medical dataset is not available. Please ensure the dataset file exists."
    
    try:
        user_input_embedding = model.encode(user_input, convert_to_tensor=True)
        disease_list = df['disease'].astype(str).tolist()
        disease_embeddings = model.encode(disease_list, convert_to_tensor=True)
        
        similarities = util.pytorch_cos_sim(user_input_embedding, disease_embeddings)[0]
        best_match_idx = int(similarities.argmax().item())
        best_match_score = float(similarities[best_match_idx].item())
    except Exception as e:
        st.error(f"Error processing query: {str(e)}")
        return "I'm sorry, there was an error processing your query. Please try again."
    
    SIMILARITY_THRESHOLD = 0.4  # Lowered threshold for better matching
    
    if best_match_score < SIMILARITY_THRESHOLD:
        # Check for keywords in user input
        for keyword, response in medical_keywords.items():
            if keyword in user_input.lower():
                return response
        
        # Enhanced fallback response
        return """I understand you're seeking medical information. While I can provide general health guidance, I don't have enough specific information about your condition to give a detailed response.

**What I recommend:**
- Consult with a qualified healthcare professional for accurate diagnosis
- Describe all your symptoms in detail
- Mention any medications you're currently taking
- Share your medical history if relevant

**For immediate concerns:**
- If experiencing severe symptoms, seek emergency medical care
- For non-emergency questions, schedule an appointment with your doctor
- Keep a symptom diary to help your healthcare provider

**General health resources:**
- Trusted medical websites (Mayo Clinic, WebMD, NHS)
- Telemedicine services for remote consultations
- Local health clinics for accessible care

Remember, this chatbot provides general information only and cannot replace professional medical advice, diagnosis, or treatment."""
    
    # Get the cure from dataset and enhance it
    try:
        row = df.iloc[best_match_idx]
        base_cure = row.get('cure', 'No treatment information available.')
        disease_name = row.get('disease', 'Unknown condition')
    except Exception:
        base_cure = 'No treatment information available.'
        disease_name = 'Unknown condition'
    
    # Create a more detailed response
    detailed_response = f"""**Condition Identified:** {disease_name}

**Recommended Treatment and Care:**

{base_cure}

**Additional Important Information:**

**General Care Guidelines:**
- Follow all prescribed medications exactly as directed
- Complete the full course of antibiotics if prescribed (even if feeling better)
- Monitor your symptoms and track any changes
- Maintain good hygiene practices to prevent spread or complications
- Get adequate rest to support your body's healing process

**When to Seek Immediate Medical Attention:**
- Symptoms worsen or don't improve within expected timeframe
- Development of new or severe symptoms
- Difficulty breathing or chest pain
- High fever that doesn't respond to medication
- Signs of allergic reaction to medications
- Any concerns about your condition

**Prevention Tips:**
- Practice good hygiene (handwashing, covering coughs/sneezes)
- Maintain a healthy lifestyle (diet, exercise, sleep)
- Stay up-to-date with vaccinations
- Avoid known triggers or risk factors
- Regular health check-ups

**Important Disclaimer:**
This information is for educational purposes only and should not replace professional medical advice. Always consult with a qualified healthcare provider for proper diagnosis and treatment. If you have a medical emergency, call emergency services immediately.

**Follow-up Care:**
- Schedule follow-up appointments as recommended
- Keep track of your symptoms and recovery progress
- Don't hesitate to contact your healthcare provider with questions
- Follow all post-treatment instructions carefully"""
    
    return detailed_response

# Function to translate text
def translate_text(text, dest_language='en'):
    try:
        translator = Translator()
        translated = translator.translate(text, dest=dest_language)
        return translated.text
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return text

# Function to generate text-to-speech audio
def text_to_speech(text, lang_code):
    try:
        # Map language codes for gTTS
        # Note: gTTS supports English, Hindi, Telugu well
        # Kannada may have limited support, will fallback to English if needed
        tts_lang_map = {
            "en": "en",  # English - Full support
            "hi": "hi",  # Hindi - Full support
            "te": "te",  # Telugu - Full support
            "kn": "kn"   # Kannada - May have limited support
        }
        
        tts_lang = tts_lang_map.get(lang_code, "en")
        
        # Try the requested language first
        try:
            tts = gtts.gTTS(text=text, lang=tts_lang, slow=False)
            audio_buffer = BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            return audio_buffer
        except Exception:
            # Fallback to English if the requested language fails
            if tts_lang != "en":
                st.info(f"⚠️ Voice output in {lang_code} not available. Using English voice instead.")
                tts = gtts.gTTS(text=text, lang="en", slow=False)
                audio_buffer = BytesIO()
                tts.write_to_fp(audio_buffer)
                audio_buffer.seek(0)
                return audio_buffer
            else:
                raise
                
    except Exception as e:
        st.warning(f"⚠️ Text-to-speech is currently unavailable. Error: {str(e)}")
        return None

# Streamlit UI
st.markdown('<h1 class="main-header">🏥 AI Health Assistant</h1>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar for language selection
with st.sidebar:
    st.header("⚙️ Settings")
    st.markdown("---")
    
    # Language selection - Only 4 languages
    language_choice = st.selectbox(
        "🌐 Select Language / भाषा चुनें / ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ / భాషను ఎంచుకోండి",
        ["English", "Hindi (हिंदी)", "Kannada (ಕನ್ನಡ)", "Telugu (తెలుగు)"]
    )
    
    st.markdown("---")
    st.markdown("### 📋 Features")
    st.markdown("- 🎯 Detailed medical responses")
    st.markdown("- 🔊 Text-to-speech support")
    st.markdown("- 🌍 Multilingual support")
    st.markdown("- 💡 Personalized health tips")
    
    st.markdown("---")
    st.markdown("### ⚠️ Disclaimer")
    st.markdown("This chatbot provides general information only and cannot replace professional medical advice.")

# Language codes mapping
language_codes = {
    "English": "en",
    "Hindi (हिंदी)": "hi",
    "Kannada (ಕನ್ನಡ)": "kn",
    "Telugu (తెలుగు)": "te"
}

# Get language code
lang_code = language_codes[language_choice]

# Main input area
st.markdown("### 💬 Ask Your Health Question")
user_input = st.text_area(
    "Describe your symptoms or ask a health-related question:",
    height=100,
    placeholder="Example: I have been experiencing fever and cough for the past 3 days..."
)

col1, col2 = st.columns([1, 1])

with col1:
    get_response_btn = st.button("🔍 Get Response", type="primary", use_container_width=True)

with col2:
    get_tip_btn = st.button("💡 Get Health Tip", use_container_width=True)

# Initialize session state for storing responses
if 'last_response' not in st.session_state:
    st.session_state.last_response = None
if 'last_response_lang' not in st.session_state:
    st.session_state.last_response_lang = None

# Process response button
if get_response_btn:
    if user_input:
        with st.spinner("🔍 Analyzing your query and finding the best response..."):
            response = find_best_cure(user_input)
            translated_response = translate_text(response, dest_language=lang_code)
            st.session_state.last_response = translated_response
            st.session_state.last_response_lang = lang_code
        
        st.markdown("---")
        st.markdown('<div class="response-box">', unsafe_allow_html=True)
        st.markdown("### 📋 Response / प्रतिक्रिया / ಪ್ರತಿಕ್ರಿಯೆ / ప్రతిస్పందన")
        st.markdown(translated_response)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Voice button
        if st.session_state.last_response:
            st.markdown("---")
            col_audio1, col_audio2 = st.columns([1, 4])
            with col_audio1:
                if st.button("🔊 Listen to Response", use_container_width=True):
                    audio_buffer = text_to_speech(st.session_state.last_response, st.session_state.last_response_lang)
                    if audio_buffer:
                        st.audio(audio_buffer, format='audio/mp3', autoplay=True)
    else:
        st.warning("⚠️ Please enter your question or symptoms first.")

# Process health tip button
if get_tip_btn:
    if user_input:
        with st.spinner("💡 Generating personalized health tip..."):
            personalized_tip = get_personalized_health_tip(user_input)
            translated_tip = translate_text(personalized_tip, dest_language=lang_code)
            st.session_state.last_response = translated_tip
            st.session_state.last_response_lang = lang_code
        
        st.markdown("---")
        st.markdown('<div class="response-box">', unsafe_allow_html=True)
        st.markdown("### 💡 Health Tip / स्वास्थ्य सुझाव / ಆರೋಗ್ಯ ಸಲಹೆ / ఆరోగ్య చిట్కా")
        st.markdown(translated_tip)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Voice button for tip
        if st.session_state.last_response:
            st.markdown("---")
            col_audio1, col_audio2 = st.columns([1, 4])
            with col_audio1:
                if st.button("🔊 Listen to Tip", use_container_width=True):
                    audio_buffer = text_to_speech(st.session_state.last_response, st.session_state.last_response_lang)
                    if audio_buffer:
                        st.audio(audio_buffer, format='audio/mp3', autoplay=True)
    else:
        st.warning("⚠️ Please enter your question or symptoms first.")

# Display last response with voice option if available
if st.session_state.last_response and not (get_response_btn or get_tip_btn):
    st.markdown("---")
    st.markdown("### 🔊 Listen to Previous Response")
    audio_buffer = text_to_speech(st.session_state.last_response, st.session_state.last_response_lang)
    if audio_buffer:
        st.audio(audio_buffer, format='audio/mp3')

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>🏥 AI Health Assistant | Providing general health information</p>
        <p><small>⚠️ This is not a substitute for professional medical advice. Always consult healthcare professionals for medical concerns.</small></p>
    </div>
    """,
    unsafe_allow_html=True
)

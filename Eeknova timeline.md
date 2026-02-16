**IDEA (new Feature)**

**1\) Wake Word (local)**

* Microphone always listening **only for “Hey Eeknova”** using **Porcupine** (offline). 

* When detected → trigger UI “assistant mode”.

**2\) UI behavior on wake**

* Avatar **zooms to close-up** (camera move \+ slight head turn toward user)

* Show overlay:

  * “Listening…”

  * Mic waveform

  * Language toggle (Auto / English / తెలుగు / हिंदी / தமிழ் / ಕನ್ನಡ)

**3\) STT (Speech-to-Text)**

* Stream recorded audio to backend:

  * Use **OpenAI Speech-to-Text** endpoint OR Azure STT. 

**4\) LLM response (your existing backend)**

* Backend sends the transcript \+ instructions:

  * “Reply in simple layman language”

  * “Use slow polite tone”

  * “If user requested native language, reply in that language; else English”

* Get response text.

**5\) TTS (Text-to-Speech)**

* Use **Azure TTS** (recommended) for Indian languages \+ SSML slow rate.   
  or **Google TTS** as alternative.   
  or **OpenAI TTS** for a unified stack. 

**6\) Facial \+ lip sync**

* Drive face using:

  * **visemes / blendshapes** (ARK64) mapped from phonemes (TTS providers can output viseme events or you can approximate)

* While speaking:

  * eye blinks, micro head nods, “listening face” → “speaking face” transitions

 **Alternatives to “Hey Eeknova” Wake Word (No Local Wake Detection)**

**🥇 Option 1: Touch / Gesture Activation (BEST for Holobox MVP)**

**How it works**

* User **taps the Holobox screen** OR

* User taps a floating **“Ask Eeknova” mic button**

* Avatar immediately:

  * zooms to close-up

  * changes expression to “listening”

  * starts voice interaction

**Why this is excellent**

* ✅ No always-on mic

* ✅ No false triggers

* ✅ Very intuitive for Indian users

* ✅ Perfect for public / community spaces

* ✅ Zero extra wake-word SDK cost

**UI pattern**

* Persistent mic icon (top-right or bottom-right)

* Optional gesture:

  * Raise hand

  * Touch avatar shoulder

  * Tap screen twice

**Recommendation**

👉 **Use this as default MVP activation**

**My Recommendation:**

1) **Wake Word**  
   Choosing option 1 touch activation for wake up

2) **UI Behavior on wake**  
* **Zoom to close-up** can be done.  
* Show overlay can be done and language toggle using **OpenAI Realtime API.**  
3) **STT**  
   Using **Realtime API** for this.  
     
4) **LLM response**  
   This can be doable by **Realtime API**  
     
5) **TTS**  
   This is also provided by OpenAI Realtime API and this API is feasible in it.

6) **Facial \+ lip sync**  
   Lip syncing was also implemented and facials will be done by blendshapes events.  
   

**Key Implementation:**

* **Speech rate:** In Realtime API there is a feature of speech rate manipulation.  
* **Language Selection UX:** This will also be done using RealTime API  
* **Privacy:** As per client desired.  
* **Fail-safe:** As per client desired.

**NOTE:** Implementation and testing will be done in 2-3 days
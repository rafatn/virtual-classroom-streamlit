import os
import streamlit as st
from livekit import api

# הגדרת עיצוב העמוד
st.set_page_config(page_title="מערכת שיעורים מקוונים", page_icon="🎓", layout="wide")

# מפתחות חיבור ל-LiveKit (ניתן לשנות או להגדיר כמשתני סביבה)
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://your-project.livekit.cloud")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "your_api_key")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "your_api_secret")

# ניהול מצב ההתחברות (Session State)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "room" not in st.session_state:
    st.session_state.room = ""
if "role" not in st.session_state:
    st.session_state.role = ""
if "token" not in st.session_state:
    st.session_state.token = ""

# --- מסך התחברות ---
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🎓 כניסה למערכת שיעורים מקוונים</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("שם מלא")
            room = st.text_input("שם השיעור / קוד חדר (למשל: math-101)")
            role_selection = st.selectbox(
                "בחר תפקיד", 
                options=["תלמיד (צפייה בלבד)", "מורה (ניהול ושידור)"]
            )
            
            submit = st.form_submit_button("הכנס לשיעור")
            
            if submit:
                if username and room:
                    role = "teacher" if "מורה" in role_selection else "student"
                    
                    # יצירת טוקן אבטחה מול LiveKit API
                    lk_api = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
                        .with_identity(username) \
                        .with_name(username) \
                        .with_grants(api.VideoGrants(
                            room_join=True,
                            room=room,
                            can_publish=(role == 'teacher'),  # למורה מותר לשדר, לתלמיד לא
                            can_subscribe=True,               # כולם יכולים לצפות
                            room_admin=(role == 'teacher')    # למורה יש הרשאות מנהל
                        ))
                    
                    st.session_state.token = lk_api.to_jwt()
                    st.session_state.username = username
                    st.session_state.room = room
                    st.session_state.role = role
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("נא למלא את כל השדות.")

# --- מסך השיעור הפעיל ---
else:
    st.title(f"📚 שיעור: {st.session_state.room}")
    st.write(f"مرحباً / שלום **{st.session_state.username}**, מחובר בתור: **{'מורה' if st.session_state.role == 'teacher' else 'תלמיד'}**")

    # כפתור יציאה מהשיעור
    if st.button("🚪 יציאה מהשיעור"):
        st.session_state.logged_in = False
        st.session_state.token = ""
        st.rerun()

    st.markdown("---")

    # שילוב נגן הוידאו של LiveKit באמצעות רכיב HTML/JS מותאם אישית ב-Streamlit
    livekit_html = f"""
    <div id="livekit-room" style="width: 100%; height: 500px; background: #1e1e1e; border-radius: 10px; overflow: hidden; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white;">
        <p id="status-text">מתחבר לשרת הוידאו...</p>
        <div id="video-container" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px; width: 100%; height: 100%; padding: 10px; box-sizing: border-box;"></div>
    </div>

    <!-- טעינת LiveKit Client SDK -->
    <script src="https://cdn.jsdelivr.net/npm/livekit-client/dist/livekit-client.umd.js"></script>
    <script>
        const url = "{LIVEKIT_URL}";
        const token = "{st.session_state.token}";
        const role = "{st.session_state.role}";

        async function run() {{
            const room = new LiveKit.Room();
            const container = document.getElementById('video-container');
            const statusText = document.getElementById('status-text');

            room.on(LiveKit.RoomEvent.TrackSubscribed, (track, publication, participant) => {{
                if (track.kind === 'video' || track.kind === 'audio') {{
                    const element = track.attach();
                    element.style.width = "100%";
                    element.style.maxHeight = "450px";
                    element.style.objectFit = "cover";
                    element.style.borderRadius = "8px";
                    container.appendChild(element);
                    statusText.style.display = 'none';
                }}
            }});

            try {{
                await room.connect(url, token);
                statusText.innerText = "מחובר בהצלחה לשיעור!";

                // אם זה מורה, הפעל מצלמה ומיקרופון אוטומטית
                if (role === 'teacher') {{
                    await room.localParticipant.enableCameraAndMicrophone();
                    room.localParticipant.trackPublications.forEach((publication) => {{
                        if (publication.track) {{
                            const element = publication.track.attach();
                            element.style.width = "100%";
                            element.style.maxHeight = "450px";
                            element.style.objectFit = "cover";
                            element.style.borderRadius = "8px";
                            container.appendChild(element);
                        }}
                    }});
                }} else {{
                    statusText.innerText = "ממתין למורה שיתחיל את השידור...";
                }}
            } catch (error) {{
                statusText.innerText = "שגיאה בהתחברות לחדר הוידאו.";
                console.error(error);
            }}
        }}

        run();
    </script>
    """

    # הצגת רכיב ה-HTML בתוך Streamlit
    st.components.v1.html(livekit_html, height=550)
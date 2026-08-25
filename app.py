import os
import streamlit as st
from livekit import api

st.set_page_config(page_title="מערכת שיעורים מקוונים", page_icon="🎓", layout="wide")

LIVEKIT_URL = st.secrets.get("LIVEKIT_URL", os.getenv("LIVEKIT_URL", "wss://your-project.livekit.cloud"))
LIVEKIT_API_KEY = st.secrets.get("LIVEKIT_API_KEY", os.getenv("LIVEKIT_API_KEY", "your_api_key"))
LIVEKIT_API_SECRET = st.secrets.get("LIVEKIT_API_SECRET", os.getenv("LIVEKIT_API_SECRET", "your_api_secret"))

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
                    
                    lk_api = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
                        .with_identity(username) \
                        .with_name(username) \
                        .with_grants(api.VideoGrants(
                            room_join=True,
                            room=room,
                            can_publish=(role == 'teacher'),
                            can_subscribe=True,
                            room_admin=(role == 'teacher')
                        ))
                    
                    st.session_state.token = lk_api.to_jwt()
                    st.session_state.username = username
                    st.session_state.room = room
                    st.session_state.role = role
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("נא למלא את כל השדות.")

else:
    st.title(f"📚 שיעור: {st.session_state.room}")
    st.write(f"שלום **{st.session_state.username}**, מחובר בתור: **{'מורה' if st.session_state.role == 'teacher' else 'תלמיד'}**")

    if st.button("🚪 יציאה מהשיעור"):
        st.session_state.logged_in = False
        st.session_state.token = ""
        st.rerun()

    st.markdown("---")

    html_template = """
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <script src="https://unpkg.com/livekit-client/dist/livekit-client.umd.min.js"></script>
    </head>
    <body style="margin:0; background:#1e1e1e; font-family:Arial, sans-serif;">
        <div id="livekit-room" style="width: 100%; height: 530px; background: #1e1e1e; border-radius: 10px; overflow: hidden; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white;">
            <div id="controls" style="margin-bottom: 15px; text-align: center;">
                <p id="status-text">לחץ על הכפתור כדי להתחבר לשידור:</p>
                <button id="connect-btn" onclick="loadAndStart()" style="padding: 12px 25px; background: #28a745; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold;">הפעל מצלמה והתחבר</button>
            </div>
            <div id="video-container" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 10px; width: 100%; height: 100%; padding: 10px; box-sizing: border-box;"></div>
        </div>

        <script>
            const url = "REPLACE_URL";
            const token = "REPLACE_TOKEN";
            const role = "REPLACE_ROLE";

            async function loadAndStart() {
                const btn = document.getElementById("connect-btn");
                const statusText = document.getElementById("status-text");
                btn.style.display = "none";
                statusText.innerText = "מתחבר לשרת הוידאו ומבקש גישה למצלמה...";

                try {
                    if (typeof LiveKit === 'undefined') {
                        throw new Error("ספריית LiveKit לא נטענה מהדפדפן. בדוק חיבור לרשת.");
                    }

                    const room = new LiveKit.Room();
                    const container = document.getElementById("video-container");

                    room.on(LiveKit.RoomEvent.TrackSubscribed, (track, publication, participant) => {
                        if (track.kind === "video" || track.kind === "audio") {
                            const element = track.attach();
                            element.style.width = "100%";
                            element.style.maxHeight = "400px";
                            element.style.objectFit = "cover";
                            element.style.borderRadius = "8px";
                            container.appendChild(element);
                        }
                    });

                    await room.connect(url, token);
                    statusText.innerText = "מחובר בהצלחה!";

                    if (role === "teacher") {
                        await room.localParticipant.enableCameraAndMicrophone();
                        room.localParticipant.trackPublications.forEach((publication) => {
                            if (publication.track) {
                                const element = publication.track.attach();
                                element.style.width = "100%";
                                element.style.maxHeight = "400px";
                                element.style.objectFit = "cover";
                                element.style.borderRadius = "8px";
                                container.appendChild(element);
                            }
                        });
                    } else {
                        statusText.innerText = "מחובר כתלמיד (האזנה וצפייה בלבד).";
                    }
                } catch (error) {
                    statusText.innerText = "שגיאה: " + (error.message || error);
                    btn.style.display = "block";
                    console.error(error);
                }
            }
        </script>
    </body>
    </html>
    """

    html_code = html_template.replace("REPLACE_URL", LIVEKIT_URL) \
                             .replace("REPLACE_TOKEN", st.session_state.token) \
                             .replace("REPLACE_ROLE", st.session_state.role)

    # שימוש ב-st.iframe המומלץ והחדש במקום st.components.v1.html
    st.iframe(srcdoc=html_code, height=560, scrolling=True)

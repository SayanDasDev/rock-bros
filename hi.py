import streamlit as st
import pandas as pd
import os
from datetime import datetime

# =============================================
# FILE CONFIGURATION
# =============================================
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.csv")
COURSES_FILE = os.path.join(DATA_DIR, "courses.csv")
ASSIGNMENTS_FILE = os.path.join(DATA_DIR, "assignments.csv")
SUBMISSIONS_FILE = os.path.join(DATA_DIR, "submissions.csv")

REQUIRED_STRUCTURE = {
    USERS_FILE: ['user_id', 'username', 'password', 'role', 'created_at'],
    COURSES_FILE: [
        'course_id', 'course_name', 'description', 'instructor', 
        'schedule', 'created_at', 'enrollment_status', 
        'image_path', 'youtube_link'  # Add these 2 new columns
    ],
    ASSIGNMENTS_FILE: ['assignment_id', 'course_id', 'title', 'description',
                      'due_date', 'max_points', 'created_at'],
    SUBMISSIONS_FILE: ['submission_id', 'assignment_id', 'student_username',
                      'submission_date', 'status', 'grade', 'feedback']
}

# =============================================
# SYSTEM INITIALIZATION
# =============================================
def initialize_system():
    """Create data directory and files with proper structure"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        
        for file_path, columns in REQUIRED_STRUCTURE.items():
            if not os.path.exists(file_path):
                pd.DataFrame(columns=columns).to_csv(file_path, index=False)
            else:
                # ========== MODIFIED SECTION ==========
                df = pd.read_csv(file_path)
                # Check for missing columns
                missing_cols = [col for col in columns if col not in df.columns]
                
                if missing_cols:
                    # Add missing columns with null values
                    for col in missing_cols:
                        df[col] = None
                    # Save updated version
                    df.to_csv(file_path, index=False)    


        # Create default admin if none exists
        users = pd.read_csv(USERS_FILE)
        if users.empty or not users[users['role'] == 'admin'].any().any():
            new_admin = pd.DataFrame([{
                'user_id': 1,
                'username': 'admin',
                'password': 'admin123',
                'role': 'admin',
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            new_admin.to_csv(USERS_FILE, mode='a', header=not os.path.exists(USERS_FILE), index=False)
    
    except Exception as e:
        st.error(f"System initialization failed: {str(e)}")
        st.stop()

# =============================================
# AUTHENTICATION SYSTEM
# =============================================
def authenticate(username, password, role):
    """Secure authentication with validation"""
    try:
        users = pd.read_csv(USERS_FILE)
        if users.empty:
            return False
            
        user = users[
            (users['username'].str.strip().str.lower() == username.strip().lower()) &
            (users['password'].astype(str).str.strip() == password.strip()) &
            (users['role'].str.strip().str.lower() == role.strip().lower())
        ]
        return not user.empty
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return False

# =============================================
# MAIN APPLICATION
# =============================================
def main():
    st.set_page_config(
        page_title="TeachIn",
        page_icon="🎓",
        layout="wide"
    )
    
    initialize_system()
    
    if 'auth' not in st.session_state:
        st.session_state.auth = {
            'logged_in': False,
            'role': None,
            'username': None
        }
    
    if not st.session_state.auth['logged_in']:
        show_login()
    else:
        show_dashboard()

def show_login():
    """Login interface with validation"""
    with st.container():
        st.markdown("<h1 style='text-align: center; color: #1e3d6b;'>🎓 TeachIn</h1>", unsafe_allow_html=True)
        
        with st.form("Login Form"):
            role = st.selectbox("Select Role", ["Student", "Teacher", "Admin"])
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Login"):
                if authenticate(username, password, role):
                    st.session_state.auth = {
                        'logged_in': True,
                        'role': role.lower(),
                        'username': username
                    }
                    st.rerun()
                else:
                    st.error("Invalid credentials or permissions")

def show_dashboard():
    """Role-based dashboard"""
    st.sidebar.title("Navigation")
    role = st.session_state.auth['role']
    username = st.session_state.auth['username']
    
    st.sidebar.header(f"Welcome, {username} ({role.title()})")
    
    # Role-based routing
    if role == 'student':
        student_dashboard()
    elif role == 'teacher':
        teacher_dashboard()
    elif role == 'admin':
        admin_dashboard()
    
    if st.sidebar.button("Logout"):
        st.session_state.auth = {'logged_in': False, 'role': None, 'username': None}
        st.rerun()

# =============================================
# DASHBOARD COMPONENTS (Partial Implementation)
# =============================================
def student_dashboard():
    menu = ["My Courses", "Assignments", "Grades", "Attendance"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    st.header(f"Student Dashboard - {choice}")
    
    if choice == "My Courses":
        courses = pd.read_csv(COURSES_FILE)
        # Filter only open courses
        available_courses = courses[courses['enrollment_status'] == 'Open']
        
        if available_courses.empty:
            st.info("No available courses found")
            return
            
        for _, row in available_courses.iterrows():
            with st.container():
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    if row['image_path'] and os.path.exists(row['image_path']):
                        st.image(row['image_path'], use_column_width=True)
                    else:
                        st.image("placeholder.jpg", use_column_width=True)
                
                with col2:
                    st.subheader(row['course_name'])
                    st.caption(f"by {row['instructor']}")
                    st.write(row['description'])
                    
                    if pd.notna(row['youtube_link']):
                        st.markdown(f"[📺 Watch on YouTube]({row['youtube_link']})")
                    
                    cols = st.columns(3)
                    cols[0].metric("Schedule", row['schedule'])
                    cols[1].metric("Status", row['enrollment_status'])
                    cols[2].metric("Created", pd.to_datetime(row['created_at']).strftime("%b %d, %Y"))
                    
                    # Add enrollment button
                    if st.button("Enroll", key=f"enroll_{row['course_id']}"):
                        st.success(f"Enrolled in {row['course_name']}!")
                
                st.markdown("---")

    elif choice == "Attendance":
        st.subheader("Attendance")
        # Fetch and display attendance data for the student
        # Placeholder implementation
        st.info("Attendance data will be displayed here.")








def teacher_dashboard():

    menu = ["My Courses", "Create Course", "Manage Content", "Attendance"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    st.header(f"Teacher Dashboard - {choice}")
    
    if choice == "My Courses":
        courses = pd.read_csv(COURSES_FILE)
        # Filter courses by current instructor
        teacher_courses = courses[courses['instructor'] == st.session_state.auth['username']]
        
        if teacher_courses.empty:
            st.info("You haven't created any courses yet")
            return
            
        for _, row in teacher_courses.iterrows():
            with st.container():
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    if row['image_path'] and os.path.exists(row['image_path']):
                        st.image(row['image_path'], use_column_width=True)
                    else:
                        st.image("placeholder.jpg", use_column_width=True)
                
                with col2:
                    st.subheader(row['course_name'])
                    st.caption(f"Status: {row['enrollment_status']}")
                    st.write(row['description'])
                    
                    if pd.notna(row['youtube_link']):
                        st.markdown(f"[📺 YouTube Playlist]({row['youtube_link']})")
                    
                    cols = st.columns(3)
                    cols[0].metric("Schedule", row['schedule'])
                    cols[1].metric("Students Enrolled", "25")  # Placeholder
                    cols[2].metric("Created", pd.to_datetime(row['created_at']).strftime("%b %d, %Y"))
                
                st.markdown("---")

    elif choice == "Attendance":
        st.subheader("Attendance")
        # Fetch and manage attendance data for the teacher's courses
        # Placeholder implementation
        st.info("Attendance management will be displayed here.")


    elif choice == "Create Course":    
        with st.form("course_creation", clear_on_submit=True):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Course Image Upload
                course_image = st.file_uploader("Course Thumbnail", 
                                               type=["jpg", "png", "jpeg"],
                                               help="Recommended size: 800x450px")
                if course_image:
                    st.image(course_image, use_column_width=True)
                
            with col2:
                # Course Details
                course_name = st.text_input("Course Title*")
                youtube_link = st.text_input("YouTube Playlist Link", 
                                            help="Paste full YouTube playlist URL")
                schedule = st.text_input("Schedule*", placeholder="Mon/Wed 10:00-11:30 AM")
                course_desc = st.text_area("Course Description*", height=150)
                enrollment_status = st.selectbox("Enrollment Status", ["Open", "Closed"])
                
                # Validation and submission
                if st.form_submit_button("Publish Course"):
                    if not all([course_name, course_desc, schedule]):
                        st.error("Please fill required fields (*)")
                    else:
                        save_course(course_name, course_desc, schedule, 
                                  enrollment_status, course_image, youtube_link)

def save_course(name, desc, schedule, status, image, yt_link):
    """Save course with media handling"""
    try:
        courses = pd.read_csv(COURSES_FILE)
        
        # Convert course_id to integers if not empty
        if not courses.empty:
            courses['course_id'] = courses['course_id'].astype(int)
            new_id = courses['course_id'].max() + 1
        else:
            new_id = 1
        
        # Handle image upload
        img_path = ""
        if image:
            os.makedirs("uploads/course_images", exist_ok=True)
            img_path = f"uploads/course_images/{new_id}_{image.name}"
            with open(img_path, "wb") as f:
                f.write(image.getbuffer())
        
        # Create course entry
        new_course = pd.DataFrame([{
            'course_id': new_id,
            'course_name': name,
            'description': desc,
            'instructor': st.session_state.auth['username'],
            'schedule': schedule,
            'enrollment_status': status,
            'youtube_link': yt_link,
            'image_path': img_path,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])
        
        new_course.to_csv(COURSES_FILE, mode='a', header=False, index=False)
        st.success("Course published successfully!")
        st.balloons()
        
    except Exception as e:
        st.error(f"Error saving course: {str(e)}")

def admin_dashboard():
    menu = ["User Management", "System Settings", "Analytics"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    st.header(f"Admin Dashboard - {choice}")
    
    if choice == "User Management":
        st.subheader("User Management")
        
        # Show existing users
        users = pd.read_csv(USERS_FILE)
        st.dataframe(users[['username', 'role', 'created_at']])
        
        # Add new user form
        with st.expander("Add New User", expanded=True):
            with st.form("user_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_username = st.text_input("Username*", help="Required field")
                    new_role = st.selectbox("Role*", ["Student", "Teacher", "Admin"])
                with col2:
                    new_password = st.text_input("Password*", type="password")
                    confirm_password = st.text_input("Confirm Password*", type="password")
                
                if st.form_submit_button("Create User"):
                    # Validation checks
                    if not all([new_username, new_password, confirm_password]):
                        st.error("Please fill all required fields (*)")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match!")
                    elif new_username.lower() in users['username'].str.lower().values:
                        st.error("Username already exists!")
                    else:
                        # Create new user
                        new_user = pd.DataFrame([{
                            'user_id': users['user_id'].max() + 1 if not users.empty else 1,
                            'username': new_username.strip(),
                            'password': new_password,
                            'role': new_role.lower(),
                            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }])
                        
                        # Save to CSV
                        new_user.to_csv(USERS_FILE, mode='a', header=False, index=False)
                        st.success(f"User {new_username} created successfully!")
                        st.rerun()

if __name__ == "__main__":
    main()
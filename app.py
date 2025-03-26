import streamlit as st
from main import *
from pdf_to_answer_dict import *
import pandas as pd

# Custom CSS for styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

* {
    font-family: 'Poppins', sans-serif;
}

.stApp {
    background-color: #f5f5f5;
}

h1, h2, h3 {
    text-align: center !important;
    color: #6a0dad !important;
}

.stButton>button {
    background-color: #6a0dad;
    color: white;
    border-radius: 8px;
    padding: 8px 16px;
    border: none;
}

.stButton>button:hover {
    background-color: #5a0c9d;
    color: white;
}

.stExpander {
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
}

.stDataFrame {
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.css-1aumxhk {
    background-color: #6a0dad;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# Background Image
background_image_url = "https://png.pngtree.com/thumb_back/fh260/background/20240104/pngtree-mystic-blackberry-a-textured-design-on-an-abstract-dark-purple-background-image_13879614.png"
page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] {{
background-image: url({background_image_url});
background-size: cover;
background-position: center;
background-repeat: no-repeat;
background-attachment: fixed;
}}

[data-testid="stAppViewContainer"]::before {{
content: "";
position: absolute;
top: 0;
left: 0;
width: 100%;
height: 100%;
background-color: rgba(0, 0, 0, 0.7);
}}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# Main App
st.title("Automated Answer Checker")
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
This app allows teachers to upload an answer key and student answer sheets for automated grading.
</div>
""", unsafe_allow_html=True)

# Upload Answer Key
st.header("📝 Upload Answer Key")
answer_key_file = st.file_uploader("Upload Answer Key (JSON format)", type="json", key="answer_key")

if answer_key_file:
    st.success("Answer key uploaded successfully!")

# Student Management
st.header("👥 Student Details")
num_students = st.number_input("Number of Students", min_value=1, max_value=50, value=1, key="num_students")

if st.button("Continue"):
    st.session_state.students = [{} for _ in range(num_students)]
    st.session_state.stage = "student_details"

# Student Answer Submission
if "stage" in st.session_state and st.session_state.stage == "student_details":
    st.header("📤 Student Answer Submission")
    
    for i in range(len(st.session_state.students)):
        with st.expander(f"Student {i + 1}", expanded=False):
            name = st.text_input(f"Full Name", key=f"name_{i}")
            roll_no = st.text_input(f"Roll Number", key=f"roll_{i}")
            pdf_files = st.file_uploader(
                f"Upload Answer PDFs",
                type=["pdf"],
                key=f"pdfs_{i}"
            )
            
            if pdf_files:
                st.session_state.students[i] = {
                    "name": name,
                    "roll_no": roll_no,
                    "pdf_files": pdf_files
                }

    if st.button("Grade All Answers"):
        st.session_state.stage = "results"

# Results Display
if "stage" in st.session_state and st.session_state.stage == "results":
    st.header("📊 Grading Results")
    
    # Create summary table
    summary_data = []
    detailed_data = []
    
    for student in st.session_state.students:
        if not student or 'pdf_files' not in student: 
            continue  # Skip if no student data or no PDFs uploaded

        try:
            # Process each PDF file for this student
            extracted_text = ""
            for pdf_file in student['pdf_files']:
                # Process the PDF (replace with your actual processing function)
                api_key = "K85286034988957"  # Your API key
                processed_text = main_st(pdf_file, answer_key_file, api_key)
                extracted_text += processed_text + "\n"
            
            # Display extracted text (optional)
            with st.expander(f"Extracted Text for {student.get('name', 'Unknown')}"):
                st.text_area("", extracted_text, height=200, key=f"text_{student['roll_no']}")
            
            # Generate example scores (replace with actual grading logic)
            scores = {"Q1": 8, "Q2": 7, "Q3": 9}  # Example scores
            total_marks = sum(scores.values())
            max_marks = len(scores) * 10  # Assuming each question is out of 10
            percentage = (total_marks / max_marks) * 100
            
            # Build student record
            student_record = {
                "Roll No": student.get('roll_no', 'N/A'),
                "Name": student.get('name', 'N/A'),
                **scores,
                "Total": total_marks,
                "Percentage": percentage
            }
            
            summary_data.append({
                "Roll No": student_record["Roll No"],
                "Name": student_record["Name"],
                "Percentage": f"{percentage:.2f}%"
            })
            
            detailed_data.append(student_record)
            
        except Exception as e:
            st.error(f"Error processing {student.get('name', 'Unknown')}: {str(e)}")
            continue
    
    # Display summary table
    st.subheader("Overall Results")
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df.style.format({"Percentage": "{:.2f}%"}),
                    use_container_width=True)
    else:
        st.warning("No student data available for display")
    
    # Detailed results in expandable section
    with st.expander("View Detailed Results", expanded=False):
        if detailed_data:
            detailed_df = pd.DataFrame(detailed_data)
            
            # Dynamically determine columns order
            base_columns = ["Roll No", "Name"]
            question_columns = [col for col in detailed_df.columns if col.startswith('Q')]
            other_columns = ["Total", "Percentage"]
            
            # Ensure columns exist before trying to reorder
            existing_columns = [col for col in base_columns + question_columns + other_columns 
                              if col in detailed_df.columns]
            
            if existing_columns:
                st.dataframe(detailed_df[existing_columns].style.format({"Percentage": "{:.2f}%"}),
                            use_container_width=True)
            else:
                st.warning("No detailed results available")
        else:
            st.warning("No detailed data available for display")
    
    if st.button("Start New Grading Session"):
        st.session_state.clear()

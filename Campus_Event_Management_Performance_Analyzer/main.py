import os
from datetime import date
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

DATA_DIR = "campus_event_data"
os.makedirs(DATA_DIR, exist_ok=True)

EVENTS_FILE = os.path.join(DATA_DIR, "events.csv")
STUDENTS_FILE = os.path.join(DATA_DIR, "students.csv")
REGISTRATIONS_FILE = os.path.join(DATA_DIR, "registrations.csv")
FEEDBACK_FILE = os.path.join(DATA_DIR, "feedback.csv")


def load_data(path, columns):
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            for col in columns:
                if col not in df.columns:
                    df[col] = pd.Series(dtype="object")
            return df[columns]
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            pass
    return pd.DataFrame(columns=columns)


def save_data(df, path):
    df.to_csv(path, index=False)


class Event:
    def __init__(self, event_id, name, event_date, venue, max_participants):
        self.event_id = str(event_id).strip()
        self.name = str(name).strip()
        self.event_date = str(event_date)
        self.venue = str(venue).strip()
        self.max_participants = int(max_participants)


class Student:
    def __init__(self, student_id, name, email):
        self.student_id = str(student_id).strip()
        self.name = str(name).strip()
        self.email = str(email).strip()


class Registration:
    def __init__(self, event_id, student_id):
        self.event_id = str(event_id).strip()
        self.student_id = str(student_id).strip()


st.set_page_config(page_title="Campus Event Manager", page_icon="🎓", layout="wide")

EVENT_COLUMNS = ["event_id", "name", "event_date", "venue", "max_participants"]
STUDENT_COLUMNS = ["student_id", "name", "email"]
REG_COLUMNS = ["event_id", "student_id", "registered_on"]
FEEDBACK_COLUMNS = ["event_id", "student_id", "rating", "comments", "submitted_on"]

events = load_data(EVENTS_FILE, EVENT_COLUMNS)
students = load_data(STUDENTS_FILE, STUDENT_COLUMNS)
registrations = load_data(REGISTRATIONS_FILE, REG_COLUMNS)
feedback = load_data(FEEDBACK_FILE, FEEDBACK_COLUMNS)


def refresh_data():
    st.session_state["refresh"] = st.session_state.get("refresh", 0) + 1
    st.rerun()


def event_participants(event_id):
    return int((registrations["event_id"].astype(str) == str(event_id)).sum())


def event_name(event_id):
    found = events[events["event_id"].astype(str) == str(event_id)]
    return found.iloc[0]["name"] if not found.empty else "Unknown event"


st.title("🎓 Campus Event Management & Feedback Analyzer")
st.caption("Manage university events, student registrations, and feedback in one place.")

# Reload persistent data on each rerun
events = load_data(EVENTS_FILE, EVENT_COLUMNS)
students = load_data(STUDENTS_FILE, STUDENT_COLUMNS)
registrations = load_data(REGISTRATIONS_FILE, REG_COLUMNS)
feedback = load_data(FEEDBACK_FILE, FEEDBACK_COLUMNS)

total_events = len(events)
total_students = len(students)
total_registrations = len(registrations)
average_rating = pd.to_numeric(feedback["rating"], errors="coerce").mean() if not feedback.empty else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Events", total_events)
m2.metric("Students", total_students)
m3.metric("Registrations", total_registrations)
m4.metric("Average rating", f"{average_rating:.2f}/5" if not pd.isna(average_rating) else "N/A")

tab_events, tab_register, tab_students, tab_feedback, tab_analytics = st.tabs(
    ["📅 Manage Events", "📝 Student Registration", "🔎 Search Students", "⭐ Feedback", "📊 Analytics"]
)

with tab_events:
    st.subheader("Create a campus event")
    with st.form("create_event_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        new_event_id = c1.text_input("Event ID", placeholder="e.g. EVT101")
        new_event_name = c2.text_input("Event name", placeholder="Tech Fest")
        event_date = c1.date_input("Event date", value=date.today())
        venue = c2.text_input("Venue", placeholder="Main Auditorium")
        max_participants = st.number_input("Maximum participants", min_value=1, max_value=100000, value=100, step=1)
        submitted = st.form_submit_button("Create Event", use_container_width=True)

        if submitted:
            if not new_event_id.strip() or not new_event_name.strip() or not venue.strip():
                st.error("Please fill in Event ID, event name, and venue.")
            elif events["event_id"].astype(str).str.casefold().eq(new_event_id.strip().casefold()).any():
                st.error("This Event ID already exists. Please use a unique ID.")
            else:
                event = Event(new_event_id, new_event_name, event_date, venue, max_participants)
                events.loc[len(events)] = [event.event_id, event.name, event.event_date, event.venue, event.max_participants]
                save_data(events, EVENTS_FILE)
                st.success(f"Event '{event.name}' created successfully.")
                st.rerun()

    st.subheader("All events")
    if events.empty:
        st.info("No events yet. Create your first event above.")
    else:
        display_events = events.copy()
        display_events["participants"] = display_events["event_id"].apply(event_participants)
        display_events["seats_left"] = pd.to_numeric(display_events["max_participants"], errors="coerce") - display_events["participants"]
        st.dataframe(display_events, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Delete an event")
    if not events.empty:
        delete_id = st.selectbox("Choose event to delete", events["event_id"].astype(str).tolist(), key="delete_event_id")
        if st.button("Delete selected event", type="secondary"):
            events = events[events["event_id"].astype(str) != str(delete_id)]
            registrations = registrations[registrations["event_id"].astype(str) != str(delete_id)]
            feedback = feedback[feedback["event_id"].astype(str) != str(delete_id)]
            save_data(events, EVENTS_FILE)
            save_data(registrations, REGISTRATIONS_FILE)
            save_data(feedback, FEEDBACK_FILE)
            st.success("Event and its related registrations/feedback were deleted.")
            st.rerun()

with tab_register:
    st.subheader("Register a student")
    with st.form("register_form", clear_on_submit=True):
        s1, s2 = st.columns(2)
        student_id = s1.text_input("Student ID", placeholder="e.g. STU001")
        student_name = s2.text_input("Student name")
        student_email = s1.text_input("Email address")
        event_options = events["event_id"].astype(str).tolist() if not events.empty else []
        selected_event = s2.selectbox("Select event", [""] + event_options, format_func=lambda x: f"{x} — {event_name(x)}" if x else "Choose an event")
        register_button = st.form_submit_button("Register Student", use_container_width=True)

        if register_button:
            sid = student_id.strip()
            if not sid or not student_name.strip() or not student_email.strip() or not selected_event:
                st.error("Fill in all fields and select a valid event.")
            elif not events["event_id"].astype(str).eq(str(selected_event)).any():
                st.error("Invalid Event ID.")
            elif registrations[
                (registrations["event_id"].astype(str) == str(selected_event)) &
                (registrations["student_id"].astype(str).str.casefold() == sid.casefold())
            ].shape[0] > 0:
                st.error("Duplicate registration: this student is already registered for this event.")
            elif event_participants(selected_event) >= int(events.loc[events["event_id"].astype(str) == str(selected_event), "max_participants"].iloc[0]):
                st.error("This event is full. Registration is closed.")
            else:
                existing = students["student_id"].astype(str).str.casefold().eq(sid.casefold())
                if existing.any():
                    students.loc[existing, ["name", "email"]] = [student_name.strip(), student_email.strip()]
                else:
                    student = Student(sid, student_name, student_email)
                    students.loc[len(students)] = [student.student_id, student.name, student.email]
                registration = Registration(selected_event, sid)
                registrations.loc[len(registrations)] = [registration.event_id, registration.student_id, date.today().isoformat()]
                save_data(students, STUDENTS_FILE)
                save_data(registrations, REGISTRATIONS_FILE)
                st.success(f"{student_name.strip()} registered for {event_name(selected_event)}.")
                st.rerun()

    st.subheader("Current registrations")
    if registrations.empty:
        st.info("No student registrations yet.")
    else:
        reg_view = registrations.merge(students, on="student_id", how="left").copy()
        reg_view["event_name"] = reg_view["event_id"].apply(event_name)
        st.dataframe(reg_view[["event_id", "event_name", "student_id", "name", "email", "registered_on"]], use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Cancel registration")
    if not registrations.empty:
        cancel_options = registrations.apply(lambda r: f'{r["event_id"]} | {r["student_id"]}', axis=1).tolist()
        cancel_choice = st.selectbox("Choose registration", cancel_options)
        if st.button("Cancel selected registration"):
            cancel_event, cancel_student = [x.strip() for x in cancel_choice.split("|", 1)]
            registrations = registrations[~(
                (registrations["event_id"].astype(str) == cancel_event) &
                (registrations["student_id"].astype(str) == cancel_student)
            )]
            save_data(registrations, REGISTRATIONS_FILE)
            st.success("Registration cancelled.")
            st.rerun()

with tab_students:
    st.subheader("Search registered students")
    search_text = st.text_input("Search by student ID, name, email, or event ID", placeholder="Type to search...")
    if not registrations.empty:
        search_view = registrations.merge(students, on="student_id", how="left")
        search_view["event_name"] = search_view["event_id"].apply(event_name)
        if search_text.strip():
            mask = search_view.astype(str).apply(lambda col: col.str.contains(search_text.strip(), case=False, na=False)).any(axis=1)
            search_view = search_view[mask]
        st.dataframe(search_view[["event_id", "event_name", "student_id", "name", "email", "registered_on"]], use_container_width=True, hide_index=True)
        st.caption(f"{len(search_view)} matching registration(s).")
    else:
        st.info("There are no registrations to search yet.")

with tab_feedback:
    st.subheader("Submit event feedback")
    if events.empty:
        st.info("Create an event before collecting feedback.")
    else:
        with st.form("feedback_form", clear_on_submit=True):
            fb_event = st.selectbox("Event", events["event_id"].astype(str).tolist(), format_func=lambda x: f"{x} — {event_name(x)}")
            fb_student = st.text_input("Student ID")
            rating = st.slider("Rating", min_value=1, max_value=5, value=5, help="1 = Poor, 5 = Excellent")
            comments = st.text_area("Comments (optional)")
            fb_submit = st.form_submit_button("Submit Feedback", use_container_width=True)
            if fb_submit:
                sid = fb_student.strip()
                registered = registrations[
                    (registrations["event_id"].astype(str) == str(fb_event)) &
                    (registrations["student_id"].astype(str).str.casefold() == sid.casefold())
                ]
                already = feedback[
                    (feedback["event_id"].astype(str) == str(fb_event)) &
                    (feedback["student_id"].astype(str).str.casefold() == sid.casefold())
                ]
                if not sid:
                    st.error("Enter your Student ID.")
                elif registered.empty:
                    st.error("Only students registered for this event can submit feedback.")
                elif not already.empty:
                    st.error("Feedback has already been submitted by this student for this event.")
                else:
                    feedback.loc[len(feedback)] = [str(fb_event), sid, int(rating), comments.strip(), date.today().isoformat()]
                    save_data(feedback, FEEDBACK_FILE)
                    st.success("Thank you! Your feedback was saved.")
                    st.rerun()

    st.subheader("Feedback records")
    if feedback.empty:
        st.info("No feedback collected yet.")
    else:
        fb_view = feedback.copy()
        fb_view["event_name"] = fb_view["event_id"].apply(event_name)
        st.dataframe(fb_view[["event_id", "event_name", "student_id", "rating", "comments", "submitted_on"]], use_container_width=True, hide_index=True)
        st.subheader("Feedback summary by event")
        summary = feedback.assign(rating=pd.to_numeric(feedback["rating"], errors="coerce")).groupby("event_id").agg(
            average_rating=("rating", "mean"), feedback_count=("rating", "count")
        ).reset_index()
        summary["event_name"] = summary["event_id"].apply(event_name)
        st.dataframe(summary[["event_id", "event_name", "average_rating", "feedback_count"]].round(2), use_container_width=True, hide_index=True)

with tab_analytics:
    st.subheader("Event participation and feedback analytics")
    if events.empty:
        st.info("Create events and register students to see analytics.")
    else:
        participation = events[["event_id", "name", "max_participants"]].copy()
        participation["participants"] = participation["event_id"].apply(event_participants)
        participation["max_participants"] = pd.to_numeric(participation["max_participants"], errors="coerce").fillna(0)
        participation["seats_left"] = participation["max_participants"] - participation["participants"]

        st.markdown("#### Event-wise participation (bar chart)")
        fig, ax = plt.subplots()
        ax.bar(participation["name"].astype(str), participation["participants"])
        ax.set_xlabel("Event")
        ax.set_ylabel("Number of participants")
        ax.set_title("Participants per Event")
        ax.tick_params(axis="x", labelrotation=30)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        st.markdown("#### Feedback rating distribution (histogram)")
        if feedback.empty:
            st.info("Submit feedback to generate the histogram.")
        else:
            ratings = pd.to_numeric(feedback["rating"], errors="coerce").dropna()
            fig2, ax2 = plt.subplots()
            ax2.hist(ratings, bins=np.arange(0.5, 6.5, 1), edgecolor="black")
            ax2.set_xticks([1, 2, 3, 4, 5])
            ax2.set_xlabel("Rating (1–5)")
            ax2.set_ylabel("Number of responses")
            ax2.set_title("Feedback Rating Distribution")
            fig2.tight_layout()
            st.pyplot(fig2)
            plt.close(fig2)

        st.markdown("#### Average rating by event")
        if feedback.empty:
            st.info("Submit feedback to see average ratings by event.")
        else:
            fb_numeric = feedback.assign(rating=pd.to_numeric(feedback["rating"], errors="coerce"))
            avg_by_event = fb_numeric.groupby("event_id")["rating"].mean().reset_index()
            avg_by_event["event_name"] = avg_by_event["event_id"].apply(event_name)
            fig3, ax3 = plt.subplots()
            ax3.bar(avg_by_event["event_name"].astype(str), avg_by_event["rating"])
            ax3.set_ylim(0, 5)
            ax3.set_xlabel("Event")
            ax3.set_ylabel("Average rating")
            ax3.set_title("Average Feedback Rating by Event")
            ax3.tick_params(axis="x", labelrotation=30)
            fig3.tight_layout()
            st.pyplot(fig3)
            plt.close(fig3)

        st.markdown("#### Participation table")
        st.dataframe(participation, use_container_width=True, hide_index=True)

st.divider()
st.caption("Data is saved locally in the campus_event_data folder as CSV files.")

import os
import shutil
import streamlit as st

from scanner.screener_engine import run_parallel_screening


# ---------------------------------
# 1. Page Configuration
# ---------------------------------
st.set_page_config(
    layout="wide",
    page_title="AI Pipeline Screener",
)

st.title("📋 High-Throughput Resume Screening Engine")
st.caption(
    "Configure job requirements, review the screening criteria, "
    "and rank candidate resumes."
)


# ---------------------------------
# 2. Job Taxonomy Form
# ---------------------------------
st.header("1. Define Job Requirements")

with st.form("job_taxonomy_form"):

    col1, col2 = st.columns(2, gap="large")

    # ---------------------------------
    # Left Column: Job Taxonomy
    # ---------------------------------
    with col1:
        st.subheader("🧩 Job Taxonomy")

        job_title = st.text_input(
            "Job Title",
            value=st.session_state.get("job_title", ""),
            placeholder="e.g. Senior Backend Engineer",
        )

        required_skills_input = st.text_area(
            "Required Skills",
            value=st.session_state.get(
                "required_skills_input",
                "Python, FastAPI, Docker, SQL",
            ),
            height=100,
            help="Essential skills, separated by commas.",
        )

        preferred_skills_input = st.text_area(
            "Preferred Skills",
            value=st.session_state.get(
                "preferred_skills_input",
                "Kubernetes, AWS, Redis, GraphQL",
            ),
            height=100,
            help="Additional desirable skills, separated by commas.",
        )

        experience_keywords_input = st.text_area(
            "Experience Keywords",
            value=st.session_state.get(
                "experience_keywords_input",
                "Senior, Lead, Architect, Production",
            ),
            height=100,
            help="Relevant experience and responsibility keywords.",
        )

    # ---------------------------------
    # Right Column: Review Configuration
    # ---------------------------------
    with col2:
        st.subheader("📋 Review Job Configuration")

        if st.session_state.get("taxonomy_saved", False):

            saved_taxonomy = st.session_state["job_taxonomy"]
            saved_weights = st.session_state["category_weights"]

            st.markdown(
                f"**Job Title:** {st.session_state['job_title']}"
            )

            st.divider()

            st.markdown("**Required Skills**")
            st.write(
                ", ".join(saved_taxonomy["required_skills"])
                or "None"
            )

            st.markdown("**Preferred Skills**")
            st.write(
                ", ".join(saved_taxonomy["preferred_skills"])
                or "None"
            )

            st.markdown("**Experience Keywords**")
            st.write(
                ", ".join(
                    saved_taxonomy["experience_keywords"]
                ) or "None"
            )

            st.divider()
            st.markdown("**Category Weights**")

            review1, review2, review3 = st.columns(3)

            with review1:
                st.metric(
                    "Required",
                    f"{saved_weights['required_skills']:.0%}",
                )

            with review2:
                st.metric(
                    "Preferred",
                    f"{saved_weights['preferred_skills']:.0%}",
                )

            with review3:
                st.metric(
                    "Experience",
                    f"{saved_weights['experience_keywords']:.0%}",
                )

        else:
            st.info(
                "Your job configuration will appear here "
                "after you save the requirements."
            )

            st.markdown("**Default screening criteria**")
            st.write("- Required skills: 50%")
            st.write("- Preferred skills: 30%")
            st.write("- Experience: 20%")

    # ---------------------------------
    # 3. Category Weights
    # ---------------------------------
    st.divider()
    st.subheader("⚖️ Category Weights")
    st.caption("The total of all three weights must equal 100%.")

    weight1, weight2, weight3 = st.columns(3)

    with weight1:
        required_weight = st.slider(
            "Required Skills (%)",
            min_value=0,
            max_value=100,
            value=st.session_state.get("required_weight", 50),
        )

    with weight2:
        preferred_weight = st.slider(
            "Preferred Skills (%)",
            min_value=0,
            max_value=100,
            value=st.session_state.get("preferred_weight", 30),
        )

    with weight3:
        experience_weight = st.slider(
            "Experience (%)",
            min_value=0,
            max_value=100,
            value=st.session_state.get("experience_weight", 20),
        )

    configure_job = st.form_submit_button(
        "💾 Save Job Requirements",
        use_container_width=True,
    )


# ---------------------------------
# 4. Validate and Save Configuration
# ---------------------------------
if configure_job:

    weights_total = (
        required_weight
        + preferred_weight
        + experience_weight
    )

    required_skills = [
        skill.strip()
        for skill in required_skills_input.split(",")
        if skill.strip()
    ]

    preferred_skills = [
        skill.strip()
        for skill in preferred_skills_input.split(",")
        if skill.strip()
    ]

    experience_keywords = [
        keyword.strip()
        for keyword in experience_keywords_input.split(",")
        if keyword.strip()
    ]

    if not job_title.strip():
        st.error("Please enter a job title.")

    elif not required_skills:
        st.error("Please enter at least one required skill.")

    elif weights_total != 100:
        st.error(
            f"Category weights must total 100%. "
            f"Current total: {weights_total}%."
        )

    else:
        st.session_state["job_title"] = job_title.strip()

        st.session_state["required_skills_input"] = (
            required_skills_input
        )
        st.session_state["preferred_skills_input"] = (
            preferred_skills_input
        )
        st.session_state["experience_keywords_input"] = (
            experience_keywords_input
        )

        st.session_state["job_taxonomy"] = {
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "experience_keywords": experience_keywords,
        }

        st.session_state["category_weights"] = {
            "required_skills": required_weight / 100,
            "preferred_skills": preferred_weight / 100,
            "experience_keywords": experience_weight / 100,
        }

        st.session_state["required_weight"] = required_weight
        st.session_state["preferred_weight"] = preferred_weight
        st.session_state["experience_weight"] = experience_weight

        st.session_state["taxonomy_saved"] = True

        st.success(
            f"Job requirements saved for "
            f"{st.session_state['job_title']}."
        )

        # Rerun to update the review panel immediately.
        st.rerun()


# ---------------------------------
# 5. Resume Upload and Screening
# ---------------------------------
if st.session_state.get("taxonomy_saved", False):

    st.divider()
    st.header("2. Upload Candidate Resumes")

    uploaded_files = st.file_uploader(
        "Upload candidate applications (PDF / DOCX)",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        help="Upload one or more candidate resumes.",
    )

    if uploaded_files:

        st.info(
            f"{len(uploaded_files)} resume(s) ready for screening."
        )

        if st.button(
            "🚀 Execute Parallel Screening Pipeline",
            type="primary",
            use_container_width=True,
        ):

            tmp_dir = "uploaded_resumes"
            os.makedirs(tmp_dir, exist_ok=True)

            saved_paths = []

            try:
                # Save each uploaded resume.
                for index, uploaded_file in enumerate(uploaded_files):

                    safe_name = os.path.basename(
                        uploaded_file.name
                    )

                    filepath = os.path.join(
                        tmp_dir,
                        f"{index}_{safe_name}",
                    )

                    with open(filepath, "wb") as file:
                        file.write(uploaded_file.getbuffer())

                    saved_paths.append(filepath)

                taxonomy = st.session_state["job_taxonomy"]
                weights = st.session_state["category_weights"]

                # Execute the existing parallel screening engine.
                with st.spinner(
                    "Processing resumes using the job taxonomy..."
                ):

                    leaderboard = run_parallel_screening(
                        saved_paths,
                        taxonomy,
                        weights,
                    )

                st.success("Resume screening completed!")

                # ---------------------------------
                # 6. Candidate Leaderboard
                # ---------------------------------
                st.divider()
                st.header("3. Candidate Leaderboard")

                if not leaderboard:
                    st.warning(
                        "No screening results were returned."
                    )

                else:
                    for rank, candidate in enumerate(
                        leaderboard,
                        start=1,
                    ):

                        filename = candidate.get(
                            "filename",
                            "Unknown candidate",
                        )

                        score = candidate.get("score", 0)
                        status = candidate.get(
                            "status",
                            "Unknown",
                        )

                        with st.expander(
                            f"🏅 Rank #{rank}: {filename} "
                            f"— Score: {score}%"
                        ):

                            st.write(
                                f"**Processing Status:** {status}"
                            )

                            if status == "Success":
                                st.subheader("Match Breakdown")

                                st.json(
                                    candidate.get("breakdown", {})
                                )

                            else:
                                st.warning(
                                    candidate.get(
                                        "error",
                                        "Unable to process this resume.",
                                    )
                                )

            except Exception as exc:
                st.error(
                    f"Screening pipeline failed: {exc}"
                )

            finally:
                shutil.rmtree(
                    tmp_dir,
                    ignore_errors=True,
                )

else:
    st.info(
        "Define and save the job taxonomy before uploading "
        "resumes for screening."
    )

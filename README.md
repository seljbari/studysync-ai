💡 What StudySync Does

StudySync is an AI-powered matching platform that helps college students find study buddies who actually match their:

Study style

Vibe

Subjects/classes

Availability

Academic goals

Grade level + major

Personality preferences

Students create a profile with their USF Student ID, upload a picture, fill out their academic details, and the app immediately:

Matches them with the most compatible student

Generates an AI explanation of why they match

Creates a friendly AI-written intro message they can send

Allows them to start a “Tinder-style” swiping experience to find additional partners

The project blends social matching with academic collaboration — designed to help students make effective study connections without the awkwardness.

🤖 How AI Enhances the Experience

We use the OpenAI API to:

✨ Explain the match

The AI reads both profiles and outputs a one-sentence reason why these two students would study well together.

✨ Generate an icebreaker message

The AI writes a casual, friendly first message the student can copy and send.

This lowers the barrier to starting collaborative studying — no more “I don’t know what to say.”

🛠️ How We Built It
Frontend

HTML, CSS, and Jinja templates for a clean, simple UI

File upload support for profile pictures

Swipe interface similar to popular matching apps

Backend

Python + Flask web application

In-memory “database” for storing user profiles

Logic for:

Matching students

Tracking likes, passes, and mutual matches

AI explanation & messaging

Swipe queue logic

Chat system architecture (partially implemented)

AI / Matching Logic

Matching score algorithm considers:

Study style similarity

Vibe compatibility

Overlapping subjects

Overlapping availability

Shared goals

Major + year alignment

AI enhances the experience but compatibility scoring is fully custom.

🚀 Core Features Completed

✔ Student sign-up with USF ID authentication
✔ Profile picture upload
✔ Smart match algorithm
✔ AI-written match explanation
✔ AI-generated intro DM
✔ “You” vs “Your Match” comparison page
✔ Swipe-style matching feature
✔ Backend logic for match requests + mutual matching
✔ Chat system structure and routing

🔧 Features In Progress

We're actively developing:

📬 Match Requests

When one student likes another, a request is sent to the other student.
If they like back → mutual match → unlock private chat.

💬 Chat System

Our backend logic for chat exists:

Stable chat IDs

Message storage

Chat rendering route

The last step is surfacing this cleanly in the UI.

🔐 Account Dashboard

Students will have:

Inbox of match requests

List of mutual matches

Links to open chats

Button to start swiping again

🧠 Challenges We Ran Into

Managing file uploads safely and storing profile images

Maintaining in-memory user data across different parts of the app

Creating a clean swipe queue without repeating users

Matching logic that feels “human,” not random

Integrating AI responses concisely and reliably

Handling server restarts while developing (lost in-memory state)

Building UI pathways from signup → match → swipe → dashboard → chat

🏆 What We’re Proud Of

We built a working, end-to-end matching pipeline in just hours

AI integration feels natural rather than forced

The UX is familiar, friendly, and actually fun to use

Profile pictures + matching logic make it feel like a real product

Students get personalized messages and recommendations instantly

The foundation is strong enough to turn into a full university tool

🔮 What’s Next for StudySync

Full database integration (Firebase / Supabase / PostgreSQL)

Persistent messaging system

Full login + dashboard experience

Notifications for new requests or matches

Matching based on course codes + schedules

Group study matching (2–5 people)

Optional personality quiz

Mobile app version

🏁 Conclusion

StudySync brings together AI, social matching, and academic collaboration into one clean tool.
It helps students find study partners who actually fit them — not just whoever happens to be nearby.

It makes studying more social, more supportive, and way less intimidating.
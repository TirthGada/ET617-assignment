// Add this inside your existing DOMContentLoaded event listener.

// --- Quiz Results Page Logic ---
const quizResultsPageTitle = document.querySelector('.quiz-results-container .page-title h1');

// Only execute this block if the quiz results page title element exists
if (quizResultsPageTitle) {
    const urlParams = new URLSearchParams(window.location.search);
    const quizId = urlParams.get('quizId'); // Get quizId from URL like ?quizId=quiz1

    if (quizId) {
        // --- In a real application, you'd use this quizId to fetch actual quiz data ---
        // Example of a fetch call:
        // fetch(`/api/quizzes/${quizId}/results`)
        //     .then(response => {
        //         if (!response.ok) {
        //             throw new Error(`HTTP error! status: ${response.status}`);
        //         }
        //         return response.json();
        //     })
        //     .then(data => {
        //         // Populate quizResultsPageTitle with the actual quiz name from data
        //         quizResultsPageTitle.textContent = `${data.quizName} - Results`;
        //         console.log('Quiz data fetched:', data);

        //         // Populate participantResultsTable with data.participants
        //         populateParticipantResults(data.participants);
        //     })
        //     .catch(error => {
        //         console.error('Error fetching quiz results:', error);
        //         quizResultsPageTitle.textContent = `Error loading Quiz ID: ${quizId}`;
        //     });


        // Placeholder for dynamic quiz name in title
        // For demonstration, let's just show the ID
        // FIX: Use backticks for template literal
        quizResultsPageTitle.textContent = `${quizId} - Results`;

        // FIX: Use backticks for template literal
        console.log(`Loading results for quiz ID: ${quizId}`);

        // Example: Dynamically update participant results (this would come from an API)
        // This is highly simplified and assumes specific elements exist
        const participantResultsTable = document.querySelector('.participant-results-table tbody');
        if (participantResultsTable) {
            // Clear existing placeholder rows if dynamically loading
            // In a real scenario, you'd clear this before adding new data
            // participantResultsTable.innerHTML = '';

            // This is a placeholder function that would be called with actual data
            // function populateParticipantResults(participants) {
            //     participantResultsTable.innerHTML = ''; // Clear previous results
            //     participants.forEach(participant => {
            //         const scorePercentage = (participant.score / participant.totalQuestions) * 100;
            //         const newRow = `
            //             <tr>
            //                 <td><span class="rank-badge ${getRankBadge(participant.rank)}">
            //                     ${getRankSymbol(participant.rank)}</span> ${participant.rank}</td>
            //                 <td>${participant.username}</td>
            //                 <td>${participant.email}</td>
            //                 <td>${participant.score}/${participant.totalQuestions}</td>
            //                 <td>
            //                     <div class="percentage-bar-container">
            //                         <div class="percentage-bar" style="width: ${scorePercentage}%;"></div>
            //                     </div>
            //                     ${scorePercentage.toFixed(0)}%
            //                 </td>
            //                 <td>${new Date(participant.timestamp).toLocaleString()}</td>
            //             </tr>
            //         `;
            //         participantResultsTable.insertAdjacentHTML('beforeend', newRow);
            //     });
            // }

            // Example of how you might add a row (if fetched from API)
            // (Uncomment and modify as needed with actual data)
            /*
            const newRow = `
                <tr>
                    <td><span class="rank-badge bronze">🥉</span> 3</td>
                    <td>newStudent</td>
                    <td>new@email.com</td>
                    <td>0/1</td>
                    <td>
                        <div class="percentage-bar-container">
                            <div class="percentage-bar grey" style="width: 0%;"></div>
                        </div>
                        0%
                    </td>
                    <td>Oct 03, 12:00</td>
                </tr>
            `;
            // participantResultsTable.insertAdjacentHTML('beforeend', newRow);
            */
        }
    } else {
        // If no quizId is found in the URL
        quizResultsPageTitle.textContent = "Quiz Results - ID Not Found";
        console.warn("No quizId found in the URL for the quiz results page.");
    }
}
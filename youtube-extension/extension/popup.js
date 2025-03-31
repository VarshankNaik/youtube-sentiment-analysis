document.addEventListener("DOMContentLoaded", async function () {
    const videoTitle = document.getElementById("video-title");
    const commentsAnalyzed = document.getElementById("comments-analyzed");

    const posPercent = document.getElementById("positive");
    const neuPercent = document.getElementById("neutral");
    const negPercent = document.getElementById("negative");

    const positiveBar = document.getElementById("positive-bar");
    const neutralBar = document.getElementById("neutral-bar");
    const negativeBar = document.getElementById("negative-bar");

    const cameraScore = document.getElementById("camera-score");
    const batteryScore = document.getElementById("battery-score");
    const performanceScore = document.getElementById("performance-score");
    const displayScore = document.getElementById("display-score");

    const sentimentChartCtx = document.getElementById("sentimentChart").getContext("2d");
    const barChartCtx = document.getElementById("barChart").getContext("2d");
    // const lineChartCtx = document.getElementById("lineChart").getContext("2d");

    commentsAnalyzed.textContent = "Fetching comments..."; // Show fetching message

    chrome.tabs.query({ active: true, currentWindow: true }, async function (tabs) {
        const videoUrl = tabs[0].url;
        try {
            const response = await fetch("http://127.0.0.1:5000/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: videoUrl })
            });

            const data = await response.json();

            if (data.error) {
                commentsAnalyzed.textContent = `Error: ${data.error}`;
                return;
            }

            // ✅ Ensure valid data for display
            const totalComments = data.total_comments || 0;
            commentsAnalyzed.textContent = `Comments Analyzed: ${totalComments}`;
            videoTitle.textContent = data.video_details?.title || "YouTube Sentiment Analysis";

            let percentages = {
                positive: data.sentiment_summary?.Positive || 0,
                neutral: data.sentiment_summary?.Neutral || 0,
                negative: data.sentiment_summary?.Negative || 0
            };

            posPercent.textContent = percentages.positive + "%";
            neuPercent.textContent = percentages.neutral + "%";
            negPercent.textContent = percentages.negative + "%";

            let total = percentages.positive + percentages.neutral + percentages.negative;

            // ✅ Avoid division by zero
            positiveBar.style.width = total > 0 ? (percentages.positive / total) * 100 + "%" : "0%";
            neutralBar.style.width = total > 0 ? (percentages.neutral / total) * 100 + "%" : "0%";
            negativeBar.style.width = total > 0 ? (percentages.negative / total) * 100 + "%" : "0%";

            // ✅ Feature Analysis (Ensuring all values exist)
            cameraScore.textContent = data.feature_analysis?.camera || 0;
            batteryScore.textContent = data.feature_analysis?.battery || 0;
            performanceScore.textContent = data.feature_analysis?.performance || 0;
            displayScore.textContent = data.feature_analysis?.display || 0;

            // ✅ Pie Chart
            new Chart(sentimentChartCtx, {
                type: "pie",
                data: {
                    labels: ["Positive", "Neutral", "Negative"],
                    datasets: [{
                        data: [percentages.positive, percentages.neutral, percentages.negative],
                        backgroundColor: ["#00ff00", "#cccccc", "#ff3333"]
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });

            // ✅ Bar Chart (Feature Analysis)
            new Chart(barChartCtx, {
                type: "bar",
                data: {
                    labels: ["Camera", "Battery", "Performance", "Display"],
                    datasets: [{
                        label: "Feature Scores",
                        data: [
                            data.feature_analysis?.camera || 0,
                            data.feature_analysis?.battery || 0,
                            data.feature_analysis?.performance || 0,
                            data.feature_analysis?.display || 0
                        ],
                        backgroundColor: ["blue", "green", "red", "purple"]
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });

            // ✅ Line Chart (Sentiment Trend Over Time)
            // if (data.sentiment_trend) {
            //     new Chart(lineChartCtx, {
            //         type: "line",
            //         data: {
            //             labels: ["Time 1", "Time 2", "Time 3", "Time 4", "Time 5"],
            //             datasets: [{
            //                 label: "Positive",
            //                 data: data.sentiment_trend?.Positive || [],
            //                 borderColor: "green",
            //                 fill: false
            //             }, {
            //                 label: "Neutral",
            //                 data: data.sentiment_trend?.Neutral || [],
            //                 borderColor: "gray",
            //                 fill: false
            //             }, {
            //                 label: "Negative",
            //                 data: data.sentiment_trend?.Negative || [],
            //                 borderColor: "red",
            //                 fill: false
            //             }]
            //         },
            //         options: { responsive: true, maintainAspectRatio: false }
            //     });
            // }

        } catch (error) {
            console.error("Error fetching data:", error);
            commentsAnalyzed.textContent = "Error fetching comments.";
        }
    });
});

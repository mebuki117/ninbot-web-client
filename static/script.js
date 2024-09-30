document.addEventListener('DOMContentLoaded', function () {
    const update = async () => {
        const res = await fetch('/events');
        if (res.status === 200) {
            const el = document.getElementById('sse-data');
            const jsonData = await res.json();

            let tableHTML = `
                <table id="sse-data">
                    <thead>
                        <tr>
                            <th>Location</th>
                            <th>%</th>
                            <th>Dist.</th>
                            <th>Nether</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            jsonData.predictions.forEach((prediction, index) => {
                let certainty = (prediction.certainty * 100).toFixed(1);
                let certaintyColor = 'green';
                if (certainty >= 30) {
                    certaintyColor = 'orange';
                } else if (certainty >= 20) {
                    certaintyColor = 'darkorange';
                } else if (certainty >= 10) {
                    certaintyColor = 'red';
                }

                tableHTML += `
                    <tr>
                        <td>(${prediction.chunkX * 16}, ${prediction.chunkZ * 16})</td>
                        <td style="color:${certaintyColor}">${certainty}%</td>
                        <td>${Math.round(prediction.overworldDistance)}</td>
                        <td>(${prediction.chunkX * 2}, ${prediction.chunkZ * 2})</td>
                    </tr>
                `;
            });

            tableHTML += `
                    </tbody>
                </table>
            `;

            el.outerHTML = tableHTML;
        }
    }

    setInterval(update, 1000);
});

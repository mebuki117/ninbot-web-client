document.addEventListener('DOMContentLoaded', function () {

    const update = async () => {
        const res = await fetch('/get_data');
        const dataDiv = document.getElementById('data');

        if (res.status === 200) {
            const jsonData = await res.json();
            console.log(jsonData)
            let tableHTML = `
                <table id="data">
                    <thead>
                        <tr>
                            <th>Location</th>
                            <th>%</th>
                            <th>Dist.</th>
                            <th>Nether</th>
                            ${showAngle(jsonData) ? "<th>Angle</th>" : ""}
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            if (jsonData.predictions.length > 0) {
                jsonData.predictions.forEach((prediction, index) => {
                    let certainty = (prediction.certainty * 100).toFixed(1);
                    let certaintyColor = getCertaintyColor(certainty);
    
                    tableHTML += `
                        <tr>
                            <td>(${prediction.x}, ${prediction.z})</td>
                            <td style="color:${certaintyColor}">${certainty}%</td>
                            <td>${Math.round(prediction.overworldDistance)}</td>
                            <td>(${prediction.netherX}, ${prediction.netherZ})</td>
                            ${showAngle(jsonData) ? `<td>${prediction.angle}</td>` : ""}
                        </tr>
                    `;
                });
            } else {
                [0,1,2,3,4].forEach(i => {
                    tableHTML += `
                        <tr>
                            <td>(---, ---)</td>
                            <td>--</td>
                            <td>---</td>
                            <td>(---, ---)</td>
                        </tr>
                    `;
                })
            }

            tableHTML += `
                    </tbody>
                </table>
            `;

            dataDiv.outerHTML = tableHTML;
        } else {
            dataDiv.innerHTML = "An error occured.<br> Is you ninbot running and has the \"Enable API\" option on?"
        }
    }

    setInterval(update, 2000);
});

const showAngle = (data) => {
    const firstPred = data?.predictions[0];
    return firstPred && firstPred.angle
}

const getCertaintyColor = (certainty) => {
    if (certainty <= 10) {
        return 'red'
    }
    if (certainty <= 20) {
        return 'orange'
    }
    if (certainty <= 50) {
        return 'yellow'
    }
    if (certainty <=70) {
        return 'lightgreen'
    }
    if (certainty <= 85) {
        return 'green'
    }

    return 'cyan'
}
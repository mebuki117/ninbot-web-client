document.addEventListener('DOMContentLoaded', function () {
    setInterval(update, 2000);
});

const update = async () => {
    const res = await fetch('/get_data');
    const dataDiv = document.getElementById('data');

    if (res.status === 200) {
        const jsonData = await res.json();
        const strongholdData = jsonData.stronghold;
        const boatState = jsonData.boat.boatState;

        let tableHTML = `
        <div id="data">
            <div id="header-bar"> 
                <h1><b>Ninjabrain Bot</b> <span>v${jsonData.version}</span></h1>
                <ul>
                    <li><img src="static/${getBoatIconFromState(boatState)}"> </img</li>
                </ul>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Location</th>
                        <th>%</th>
                        <th>Dist.</th>
                        <th>Nether</th>
                        ${shouldShowAngle(strongholdData) ? "<th>Angle</th>" : ""}
                    </tr>
                </thead>
                <tbody>
        `;
        
        if (strongholdData.predictions.length > 0) {
            strongholdData.predictions.forEach((prediction, index) => {
                let certainty = (prediction.certainty * 100).toFixed(1);
                let certaintyColor = getCertaintyColor(certainty);

                tableHTML += `
                    <tr>
                        <td>(${prediction.x}, ${prediction.z})</td>
                        <td style="color:${certaintyColor}">${certainty}%</td>
                        <td>${Math.round(prediction.overworldDistance)}</td>
                        <td>(${prediction.netherX}, ${prediction.netherZ})</td>
                        ${shouldShowAngle(strongholdData) ? `<td>${prediction.angle}</td>` : ""}
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
            </div>
        `;

        dataDiv.outerHTML = tableHTML;
    } else {
        dataDiv.innerHTML = "An error occured.<br> Is you ninbot running and has the \"Enable API\" option on?"
    }
}

const shouldShowAngle = (data) => {
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

const getBoatIconFromState = (state) => {
    switch (state) {
        case 'NONE':
            return 'boat_gray.png'
        case 'ERROR':
            return 'boat_red.png'
        case 'MEASURING':
            return 'boat_blue.png'
        case 'VALID':
            return 'boat_green.png'
    }
}
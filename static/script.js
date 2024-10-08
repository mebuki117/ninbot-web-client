document.addEventListener('DOMContentLoaded', function () {
    const update = async () => {
        const res = await fetch('/get_data');
        const dataDiv = document.getElementById('data');

        if (res.ok || (res.status >= 501 && res.status <= 504)) {
            const jsonData = await res.json();
            console.log(jsonData);
            dataDiv.outerHTML = generateTable(jsonData, res.status);
        } else {
            dataDiv.innerHTML = "An error occurred.<br> Is your ninbot running and has the \"Enable API\" option on?";
        }
    }

    const generateTable = (jsonData, status) => {
        if (status >= 200 && status <= 204) {
            return generateStrongholdTable(jsonData, status);
        } else if (status >= 206 && status <= 209) {
            return generateMisreadMessageTable(jsonData, status);
        } else if (status >= 210 && status <= 214) {
            return generateBlindTable(jsonData, status);
        } else if (status >= 501 && status <= 504) {
            return generateIdleTable(jsonData, status);
        }
        return '';
    }

    const generateStrongholdTable = (jsonData, status) => {
        const boatstatus = showAngle(jsonData) ? "" : getStatusSymbol(status);
        let tableHTML = `
            <table id="data">
                <thead>
                    <tr>
                        <th>${toggle_LocationChunk(jsonData) ? 'Chunk' : 'Location'}</th>
                        <th>%</th>
                        <th>Dist.</th>
                        <th>Nether${boatstatus}</th>
                        ${showAngle(jsonData) ? `<th>Angle${getStatusSymbol(status)}</th>` : ""}
                    </tr>
                </thead>
                <tbody>
        `;

        if (jsonData.predictions.length > 0) {
            jsonData.predictions.forEach(prediction => {
                const certainty = (prediction.certainty * 100).toFixed(1);
                const certaintyColor = getCertaintyColor(certainty);

                tableHTML += `
                    <tr>
                        <td>(${prediction.x}, ${prediction.z})</td>
                        <td style="color:${certaintyColor}">${certainty}%</td>
                        <td>${Math.round(prediction.overworldDistance)}</td>
                        <td>(${prediction.netherX}, ${prediction.netherZ})</td>
                        <td>
                            ${showAngle(jsonData) ? 
                                `${prediction.angle}
                                <span style="color: ${getColorForDirection(prediction.direction)};">
                                    (${prediction.direction ? (prediction.direction > 0 ? "-> " : "<- ") + Math.abs(prediction.direction).toFixed(1) : "N/A"})
                                </span>` 
                            : ""}
                    </tr>
                `;
            });
        }

        tableHTML += `
                </tbody>
            </table>
        `;

        return tableHTML;
    }

    const generateMisreadMessageTable = (jsonData, status) => {
        const boatstatus = showAngle(jsonData) ? "" : getStatusSymbol(status);
        return `
            <table id="data">
                <thead>
                    <th>Blind${boatstatus}</th>
                </thead>
                <tbody>
                    <tr><td>Could not determine the stronghold chunk.</td></tr>
                    <tr><td>You probably misread one of the eyes.</td></tr>
                    ${Array(3).fill().map(() => `<tr><td>---</td></tr>`).join('')}
                </tbody>
            </table>
        `;
    }

    const generateBlindTable = (jsonData, status) => {
        const boatstatus = showAngle(jsonData) ? "" : getStatusSymbol(status);
        let tableHTML = `
            <table id="data">
                <thead>
                    <th>Blind${boatstatus}</th>
                </thead>
                <tbody>
        `;

        if (jsonData.blindResult) {
            const blind = jsonData.blindResult;
            const evaluation = blind.evaluation;
            const evaluationColor = getevaluationColor(evaluation);

            tableHTML += `
                <tr>
                    <td>Blind coords (${blind.xInNether}, ${blind.zInNether}) are <span style="color:${evaluationColor}">${evaluation}</span></td>
                </tr>
                <tr>
                    <td><span style="color:${evaluationColor}">${blind.highrollProbability}</span> chance of <400 block blind</td>
                </tr>
                <tr>
                    <td>${blind.improveDirection}°, ${blind.improveDistance} blocks away, for better boords</td>
                </tr>
            `;
            tableHTML += Array(2).fill().map(() => `<tr><td>---</td></tr>`).join('');
        }

        tableHTML += `
                </tbody>
            </table>
        `;

        return tableHTML;
    }

    const generateIdleTable = (jsonData, status) => {
        const boatstatus = showAngle(jsonData) ? "" : getStatusSymbol(status);
        let tableHTML = `
            <table id="data">
                <thead>
                    <tr>
                        <th>${toggle_LocationChunk(jsonData) ? 'Chunk' : 'Location'}</th>
                        <th>%</th>
                        <th>Dist.</th>
                        <th>Nether${boatstatus}</th>
                        ${showAngle(jsonData) ? `<th>Angle${getStatusSymbol(status)}</th>` : ""}
                    </tr>
                </thead>
                <tbody>
        `;

        [0, 1, 2, 3, 4].forEach(() => {
            tableHTML += `
                <tr>
                    <td>(---, ---)</td>
                    <td>--</td>
                    <td>---</td>
                    <td>(---, ---)</td>
                    ${showAngle(jsonData) ? `<td>---</td>` : ""}
                </tr>
            `;
        });

        tableHTML += `
                </tbody>
            </table>
        `;

        return tableHTML;
    }

    const getStatusSymbol = (status) => {
        switch (status) {
            case 201:
            case 206:
            case 211:
            case 501:
                return " ⚫";
    
            case 202:
            case 207:
            case 212:
            case 502:
                return " 🔵"; 
    
            case 203:
            case 208:
            case 213:
            case 503:
                return " 🟢";
    
            case 204:
            case 209:
            case 214:
            case 504:
                return " 🔴";
    
            default:
                return "";
        }
    }

    setInterval(update, 500);
});

const showAngle = (data) => {
    const firstPred = data?.predictions && Array.isArray(data.predictions) ? data.predictions[0] : null;
    return (firstPred && firstPred.angle) || (data?.angle === true);
}

const toggle_LocationChunk = (data) => {
    const firstPred = data?.predictions[0];
    return firstPred && firstPred.useChunk
}

const getCertaintyColor = (certainty) => {
    if (50 <= certainty) {
        return getColors('#d8c064', '#59b94b', 51, Math.floor(certainty-50));
    } else {
        return getColors('#bd4141', '#d8c064', 51, Math.floor(certainty));
    }
}

const getColorForDirection = (direction) => {
    const absdirection = Math.abs(direction);
    let color;

    if (absdirection <= 180) {
        color = getColors('#bd4141', '#59b94b', 181, Math.floor(180 - absdirection));
    } else {
        color = '#d8c064';
    }

    return color;
}

function hexToRgb(hexColor) {
    hexColor = hexColor.replace('#', '');
    return [
        parseInt(hexColor.substring(0, 2), 16),
        parseInt(hexColor.substring(2, 4), 16),
        parseInt(hexColor.substring(4, 6), 16)
    ];
}

function rgbToHex(rgbColor) {
    return `#${((1 << 24) + (rgbColor[0] << 16) + (rgbColor[1] << 8) + rgbColor[2]).toString(16).slice(1)}`;
}

function interpolateColors(color1, color2, steps) {
    const rgb1 = hexToRgb(color1);
    const rgb2 = hexToRgb(color2);
    const interpolatedColors = [];

    for (let step = 0; step < steps; step++) {
        const r = Math.round(rgb1[0] + (rgb2[0] - rgb1[0]) * step / (steps - 1));
        const g = Math.round(rgb1[1] + (rgb2[1] - rgb1[1]) * step / (steps - 1));
        const b = Math.round(rgb1[2] + (rgb2[2] - rgb1[2]) * step / (steps - 1));
        interpolatedColors.push(rgbToHex([r, g, b]));
    }
    return interpolatedColors;
}

function getColors(color1, color2, steps, getstep) {
    const colors = interpolateColors(color1, color2, steps);
    return colors[getstep];
}

const evaluationColors = {
    'excellent': { color1: '#d8c064', color2: '#59b94b', steps: 51, step: 50 },
    'good for highroll': { color1: '#d8c064', color2: '#59b94b', steps: 51, step: 40 },
    'okay for highroll': { color1: '#d8c064', color2: '#59b94b', steps: 51, step: 25 },
    'bad, but in ring': { color1: '#d8c064', color2: '#59b94b', steps: 51, step: 0 },
    'bad': { color1: '#bd4141', color2: '#d8c064', steps: 51, step: 25 },
    'not in any ring': { color1: '#bd4141', color2: '#d8c064', steps: 51, step: 0 }
};

const getevaluationColor = (evaluation) => {
    const colorInfo = evaluationColors[evaluation];
    if (colorInfo) {
        return getColors(colorInfo.color1, colorInfo.color2, colorInfo.steps, colorInfo.step);
    }
    return '#FFFFFF'
}
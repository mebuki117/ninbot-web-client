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
        if (status >= 200 && status <= 203) {
            return generateStrongholdTable(jsonData, status);
        } else if (status >= 205 && status <= 208) {
            return generateMisreadMessageTable(jsonData, status);
        } else if (status >= 210 && status <= 213) {
            return generateBlindTable(jsonData, status);
        } else if (status >= 215 && status <= 218) {
            return generateDivineTable(jsonData, status);
        } else if (status >= 500 && status <= 503) {
            return generateIdleTable(jsonData, status);
        }
        return '';
    }

    const createTableHTML = (headers, bodyRows) => `
        <table id="data">
            <thead>
                <tr>${headers.map(header => `<th>${header}</th>`).join('')}</tr>
            </thead>
            <tbody>
                ${bodyRows.join('')}
            </tbody>
        </table>
    `;

    const generateRowHTML = (cells) => `
        <tr>${cells.map(cell => `<td>${cell}</td>`).join('')}</tr>
    `;

    const generateStrongholdTable = (jsonData, status) => {
        const boatState = showAngle(jsonData) ? "" : getStatusSymbol(status);
        const headers = [
            toggle_LocationChunk(jsonData) ? 'Chunk' : 'Location',
            '%', 'Dist.', `Nether${boatState}`,
            showAngle(jsonData) ? `Angle${getStatusSymbol(status)}` : ""
        ].filter(Boolean);

        const bodyRows = jsonData.predictions.map(prediction => {
            const certainty = (prediction.certainty * 100).toFixed(1);
            const certaintyColor = getCertaintyColor(certainty);

            const angleHTML = showAngle(jsonData) ? 
                `${prediction.angle}
                <span style="color: ${getColorForDirection(prediction.direction)};">
                    (${prediction.direction ? (prediction.direction > 0 ? "-> " : "<- ") + Math.abs(prediction.direction).toFixed(1) : "N/A"})
                </span>` 
                : "";

            return generateRowHTML([
                `(${prediction.x}, ${prediction.z})`,
                `<span style="color:${certaintyColor}">${certainty}%</span>`,
                `${Math.round(prediction.overworldDistance)}`,
                `(${prediction.netherX}, ${prediction.netherZ})`,
                angleHTML
            ]);
        });

        return createTableHTML(headers, bodyRows);
    }

    const generateMisreadMessageTable = (jsonData, status) => {
        const boatState = showAngle(jsonData) ? "" : getStatusSymbol(status);
        const headers = [`Blind${boatState}`];

        const bodyRows = [
            generateRowHTML(["Could not determine the stronghold chunk."]),
            generateRowHTML(["You probably misread one of the eyes."]),
            ...Array(3).fill(generateRowHTML(["&nbsp;"]))
        ];

        return createTableHTML(headers, bodyRows);
    }

    const generateBlindTable = (jsonData, status) => {
        const boatState = showAngle(jsonData) ? "" : getStatusSymbol(status);
        const headers = [`Blind${boatState}`];
        const bodyRows = [];

        if (jsonData.blindResult) {
            const blind = jsonData.blindResult;
            const evaluationColor = getevaluationColor(blind.evaluation);

            bodyRows.push(generateRowHTML([
                `Blind coords (${blind.xInNether}, ${blind.zInNether}) are <span style="color:${evaluationColor}">${blind.evaluation}</span>`
            ]));
            bodyRows.push(generateRowHTML([
                `<span style="color:${evaluationColor}">${blind.highrollProbability}</span> chance of <400 block blind`
            ]));
            bodyRows.push(generateRowHTML([
                `${blind.improveDirection}°, ${blind.improveDistance} blocks away, for better coords`
            ]));
            bodyRows.push(...Array(2).fill(generateRowHTML(["---"])));
        }

        return createTableHTML(headers, bodyRows);
    }

    const generateDivineTable = (jsonData, status) => {
        const boatState = showAngle(jsonData) ? "" : getStatusSymbol(status);
        const divineResult = jsonData.divineResult;

        const headers = [
            `Fossile ${divineResult.fossilXCoordinate}`, 's1', 's2', `s3${boatState}`
        ];

        const bodyRows = [
            generateRowHTML(['Safe:', ...[0, 1, 2].map(index => `(${getDivineCoord(divineResult.formattedSafeCoords, index)})`)]),
            generateRowHTML(['Highroll:', ...[0, 1, 2].map(index => `(${getDivineCoord(divineResult.formattedHighrollCoords, index)})`)]),
            ...Array(3).fill(generateRowHTML(['&nbsp;', '&nbsp;', '&nbsp;', '&nbsp;']))
        ];

        return createTableHTML(headers, bodyRows);
    }

    const generateIdleTable = (jsonData, status) => {
        const boatState = showAngle(jsonData) ? "" : getStatusSymbol(status);
        const headers = [
            toggle_LocationChunk(jsonData) ? 'Chunk' : 'Location',
            '%', 'Dist.', `Nether${boatState}`,
            showAngle(jsonData) ? `Angle${getStatusSymbol(status)}` : ""
        ].filter(Boolean);

        const bodyRows = Array(5).fill(generateRowHTML([
            '&nbsp;', '&nbsp;', '&nbsp;', '&nbsp;', showAngle(jsonData) ? '&nbsp;' : ''
        ]));

        return createTableHTML(headers, bodyRows);
    }

    const getStatusSymbol = (status) => {
        switch (status) {
            case 200:
            case 205:
            case 210:
            case 215:
            case 500:
                return " ⚫";
    
            case 201:
            case 206:
            case 211:
            case 216:
            case 501:
                return " 🔵"; 
    
            case 202:
            case 207:
            case 212:
            case 217:
            case 502:
                return " 🟢";
    
            case 203:
            case 208:
            case 213:
            case 218:
            case 503:
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
    const firstPred = data?.predictions?.[0];
    const useChunkvalue = firstPred ? firstPred.useChunk : data?.useChunk;
    return useChunkvalue || false;
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

const getDivineCoord = (coords, index) => {
    const coordsArray = coords.split("), (").map(coord => coord.replace(/[()]/g, '').trim());

    if (index >= 0 && index < coordsArray.length) {
        return coordsArray[index];
    } else {
        return null;
    }
}
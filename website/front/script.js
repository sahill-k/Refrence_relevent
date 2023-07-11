const mainBody = document.querySelector('.main-body')
const fileInput = document.querySelector('#file');
const fileForm = document.querySelector("#file-form")
fileInput.addEventListener('change', handleUpload);



async function handleUpload()
{
    const form = new FormData(fileForm)
    let response = await fetch('http://127.0.0.1:5000/upload', {
        method: 'POST',
        body: form
    });
    let result = await response.json();
    console.log(result)
    show_progress(result["time"])
    setTimeout(() => {
        get_similarity(result['file_id'])
    }, result["time"]*1000)
}

async function get_similarity(tag)
{
    let response = await fetch("http://127.0.0.1:5000/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({"tag": tag})
    })
    let result = await response.json()
    show_results(result['refs_selected'], result['similarity'])
}

function show_results(titles, similarity)
{
    mainBody.innerHTML = `<div class="result-holder"><div class="reference-heading">References</div><div class="similarity-heading">Similarity</div><div class="results"></div></div>`
    const resultsHolder = document.querySelector('.results');
    for (let i = 0; i < titles.length; i++)
    {
        const resultItem = document.createElement('div');
        const title = document.createElement('div');
        const sim = document.createElement('div');
        resultItem.classList.add("result-item");
        title.classList.add("title");
        sim.classList.add("similarity");
        title.innerText = titles[i];
        sim.innerText = similarity[i];
        resultItem.appendChild(title);
        resultItem.appendChild(sim);
        resultsHolder.appendChild(resultItem);
    }
}

function show_progress(time)
{
    mainBody.innerHTML = `<div class="loading-bar-holder"><div class="description">This might take a while. Get a cup of coffee.</div><div class="loading-bar-outer"><div class="loading-bar-inner"></div></div></div>`
    const loadingBar = document.querySelector(".loading-bar-inner");
    let width = 0.1;
    const interval = setInterval(fillBar, time)
    function fillBar(){
        if (width >= 100){
            console.log("Finish")
            clearInterval(interval);
        }
        else{
            width = width + 0.1;
            loadingBar.style.width = width + "%";
        }
    }

}


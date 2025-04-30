document.addEventListener("DOMContentLoaded", function () {
    let loading = document.getElementById("loading");

    function showLoading() {
        loading.style.display = "block";
    }

    function hideLoading() {
        loading.style.display = "none";
    }

    showLoading();
    
    setTimeout(() => {
        hideLoading();
    }, 2000); // Скрываем через 2 секунды
});

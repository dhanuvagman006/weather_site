const apiKey = "86975ceb4f37fb37483f7e8327399d87"; // Replace with your actual API key

async function getWeather() {
  const city = document.getElementById("cityInput").value;
  if (!city) return;
  const response = await fetch(
    `https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${apiKey}&units=metric`
  );
  const data = await response.json();
  displayWeather(data);
  fetchForecast(data.coord.lat, data.coord.lon);
  fetchWeeklyForecast(data.coord.lat, data.coord.lon);
  updateMap(data.coord.lat, data.coord.lon);
  saveFavorite(city);
}

async function getLocationWeather() {
  navigator.geolocation.getCurrentPosition(async (position) => {
    const { latitude, longitude } = position.coords;
    const response = await fetch(
      `https://api.openweathermap.org/data/2.5/weather?lat=${latitude}&lon=${longitude}&appid=${apiKey}&units=metric`
    );
    const data = await response.json();
    displayWeather(data);
    fetchForecast(latitude, longitude);
    fetchWeeklyForecast(latitude, longitude);
    updateMap(latitude, longitude);
  });
}

function displayWeather(data) {
    const result = document.getElementById("result");
    result.classList.remove("hidden");
  
    const icon = `https://openweathermap.org/img/wn/${data.weather[0].icon}@2x.png`;
    const localTime = new Date(data.dt * 1000).toLocaleString("en-US", {
      timeZone: data.timezone ? `GMT${data.timezone / 3600}` : "UTC",
      weekday: "long", year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"
    });
  
    result.innerHTML = `
      <div class="flex justify-between items-center mb-2">
        <h2 class="text-xl font-bold">${data.name}, ${data.sys.country}</h2>
        <img src="${icon}" alt="icon" class="w-12 h-12">
      </div>
      <p class="text-sm italic mb-4 text-gray-500">${localTime}</p>
      <p class="text-lg">🌡️ ${data.main.temp}°C | Feels like ${data.main.feels_like}°C</p>
      <p class="text-md text-gray-600 dark:text-gray-300">💧 Humidity: ${data.main.humidity}%</p>
      <p class="text-md text-gray-600 dark:text-gray-300">🌬️ Wind: ${data.wind.speed} m/s</p>
      <p class="text-md mt-2 italic text-gray-500">${data.weather[0].description}</p>
    `;
  }
  

async function fetchForecast(lat, lon) {
  const response = await fetch(
    `https://api.openweathermap.org/data/2.5/forecast?lat=${lat}&lon=${lon}&appid=${apiKey}&units=metric`
  );
  const data = await response.json();
  const labels = [];
  const temps = [];

  data.list.forEach((entry, index) => {
    if (index % 8 === 0) {
      labels.push(new Date(entry.dt_txt).toLocaleDateString("en-US", { weekday: "short" }));
      temps.push(entry.main.temp);
    }
  });

  const ctx = document.getElementById("forecastChart").getContext("2d");
  document.getElementById("forecastChart").classList.remove("hidden");

  if (window.myChart) window.myChart.destroy();
  window.myChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Temp (°C)",
        data: temps,
        borderColor: "#3b82f6",
        backgroundColor: "#3b82f688",
        fill: true,
        tension: 0.3,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
    },
  });
}

function updateMap(lat, lon) {
  const mapDiv = document.getElementById("map");
  mapDiv.classList.remove("hidden");

  if (window.weatherMap) {
    window.weatherMap.setView([lat, lon], 10);
    return;
  }

  window.weatherMap = L.map("map").setView([lat, lon], 10);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
  }).addTo(window.weatherMap);
  L.marker([lat, lon]).addTo(window.weatherMap);
}

async function fetchWeeklyForecast(lat, lon) {
  const today = new Date().toISOString().split("T")[0];
  const nextWeek = new Date(Date.now() + 6 * 86400000).toISOString().split("T")[0];

  const res = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=auto&start_date=${today}&end_date=${nextWeek}`);
  const data = await res.json();
  if (!data.daily) return;

  const container = document.getElementById("weeklyForecast");
  container.innerHTML = "";
  container.classList.remove("hidden");

  data.daily.time.forEach((date, i) => {
    const max = data.daily.temperature_2m_max[i];
    const min = data.daily.temperature_2m_min[i];
    const code = data.daily.weathercode[i];
    const icon = getWeatherIcon(code);

    const day = new Date(date).toLocaleDateString("en-US", { weekday: "short" });

    const card = document.createElement("div");
    card.className = "p-4 min-w-[120px] glassmorphism rounded-xl flex flex-col items-center shadow-md";
    card.innerHTML = `
      <div class="text-sm text-gray-500 dark:text-gray-400">${day}</div>
      <img src="${icon}" alt="icon" class="w-8 h-8 my-2">
      <div class="text-md font-semibold">${max}° / ${min}°</div>
    `;
    container.appendChild(card);
  });
}

function getWeatherIcon(code) {
  const icons = {
    0: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/clear-day.svg",
    1: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/mostly-clear-day.svg",
    2: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/partly-cloudy-day.svg",
    3: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/cloudy.svg",
    45: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/fog.svg",
    48: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/fog.svg",
    51: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/drizzle.svg",
    61: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/rain.svg",
    71: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/snow.svg",
    80: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/showers-day.svg",
    95: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/thunderstorms.svg",
  };
  return icons[code] || icons[3];
}

function toggleTheme() {
  document.documentElement.classList.toggle("dark");
}

function saveFavorite(city) {
  let favorites = JSON.parse(localStorage.getItem("favorites") || "[]");
  if (!favorites.includes(city)) {
    favorites.push(city);
    localStorage.setItem("favorites", JSON.stringify(favorites));
    loadFavorites();
  }
}

function loadFavorites() {
  const favorites = JSON.parse(localStorage.getItem("favorites") || "[]");
  const select = document.getElementById("favoriteCities");
  select.innerHTML = '<option value="">Select a favorite city</option>';
  favorites.forEach(city => {
    const option = document.createElement("option");
    option.value = city;
    option.textContent = city;
    select.appendChild(option);
  });
}

function selectFavorite(el) {
  if (el.value) {
    document.getElementById("cityInput").value = el.value;
    getWeather();
  }
}

// Initialize on page load
loadFavorites();

// #Scenario2 
// #Design an IIOT System for monitoring the performance of industrial machinery ,such as sensors measuring vibration,temperature and pressure.How would you collect ,process and analyze this data in real-time to predict potential failures?
// #Programing focus-Data Streaming(e,g, kafka,Apache,Flink),edge computing ,machine learning algorithms
// #(eg.,anomaly detection),and realtime dashboards.

//Question
// Develope a c++ program that reads data from a sensor,perform basic data processing(e.g.,averaging.filtering) and transmits the results to a central server using a secure communication protocol(e.g..LS/SSL)

//Programing Focus:C++ ,sensors liabraries,nerworking,security protocols




#include <iostream>
#include <vector>
#include <numeric>
#include <thread>
#include <chrono>
#include <curl/curl.h>
#include <cstdlib>
#include <ctime>

struct SensorData {
    float vibration;
    float temperature;
    float pressure;
};

SensorData readSensorData() {
    SensorData data;
    data.vibration = 0.5f + static_cast<float>(rand()) / (static_cast<float>(RAND_MAX / 5.0f));
    data.temperature = 20.0f + static_cast<float>(rand()) / (static_cast<float>(RAND_MAX / 15.0f));
    data.pressure = 1.0f + static_cast<float>(rand()) / (static_cast<float>(RAND_MAX / 2.0f));
    return data;
}

float calculateAverage(const std::vector<float>& values) {
    if (values.empty()) return 0.0f;
    float sum = std::accumulate(values.begin(), values.end(), 0.0f);
    return sum / values.size();
}

void sendToServer(const SensorData& data) {
    CURL* curl;
    CURLcode res;

    curl = curl_easy_init();
    if (curl) {
        std::string jsonPayload = "{\"vibration\":" + std::to_string(data.vibration) +
                                  ",\"temperature\":" + std::to_string(data.temperature) +
                                  ",\"pressure\":" + std::to_string(data.pressure) + "}";

        curl_easy_setopt(curl, CURLOPT_URL, "https://yourserver.com/api/sensordata");
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, jsonPayload.c_str());
        curl_easy_setopt(curl, CURLOPT_USE_SSL, CURLUSESSL_ALL);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 1L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 2L);

        struct curl_slist* headers = nullptr;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        res = curl_easy_perform(curl);
        if (res != CURLE_OK)
            std::cerr << "Failed to send data: " << curl_easy_strerror(res) << std::endl;
        else
            std::cout << "Data sent successfully." << std::endl;

        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
    }
}

int main() {
    srand(static_cast<unsigned int>(time(0)));

    const int windowSize = 5;
    std::vector<float> vibrationWindow, temperatureWindow, pressureWindow;

    while (true) {
        SensorData raw = readSensorData();

        vibrationWindow.push_back(raw.vibration);
        temperatureWindow.push_back(raw.temperature);
        pressureWindow.push_back(raw.pressure);

        if (vibrationWindow.size() > windowSize) vibrationWindow.erase(vibrationWindow.begin());
        if (temperatureWindow.size() > windowSize) temperatureWindow.erase(temperatureWindow.begin());
        if (pressureWindow.size() > windowSize) pressureWindow.erase(pressureWindow.begin());

        SensorData processed;
        processed.vibration = calculateAverage(vibrationWindow);
        processed.temperature = calculateAverage(temperatureWindow);
        processed.pressure = calculateAverage(pressureWindow);

        std::cout << "Processed Sensor Data => "
                  << "Vibration: " << processed.vibration << "g, "
                  << "Temperature: " << processed.temperature << "°C, "
                  << "Pressure: " << processed.pressure << "atm\n";

        sendToServer(processed);

        std::this_thread::sleep_for(std::chrono::seconds(5));
    }

    return 0;
}
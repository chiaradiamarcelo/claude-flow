package banking.application

import com.fasterxml.jackson.databind.ObjectMapper
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse

class SyncExchangeRatesUseCase(
    private val http: HttpClient,
    private val mapper: ObjectMapper,
    private val cache: MutableMap<String, Double>,
) {
    fun execute() {
        val response = http.send(
            HttpRequest.newBuilder(URI.create("https://rates.example.com/latest")).build(),
            HttpResponse.BodyHandlers.ofString(),
        )
        val rates: Map<String, Double> = mapper.readValue(response.body(), Map::class.java) as Map<String, Double>
        cache.clear()
        cache.putAll(rates)
    }
}

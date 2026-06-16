package banking.api

import banking.api.dto.OpenAccountRequest
import banking.api.dto.AccountResponse
import banking.application.OpenAccountUseCase
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RestController
import java.net.URI

@RestController
class OpenAccountController(
    private val openAccount: OpenAccountUseCase,
) {

    @PostMapping("/accounts")
    fun open(@RequestBody request: OpenAccountRequest): ResponseEntity<AccountResponse> {
        val accountId = openAccount.execute(request.ownerId, request.initialBalanceCents)
        val body = AccountResponse(accountId, request.initialBalanceCents)
        return ResponseEntity.created(URI.create("/accounts/$accountId")).body(body)
    }
}

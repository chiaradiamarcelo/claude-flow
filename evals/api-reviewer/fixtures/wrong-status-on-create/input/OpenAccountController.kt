package banking.api

import banking.api.dto.OpenAccountRequest
import banking.api.dto.AccountResponse
import banking.application.OpenAccountUseCase
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RestController

@RestController
class OpenAccountController(
    private val openAccount: OpenAccountUseCase,
) {

    @PostMapping("/accounts")
    fun open(@RequestBody request: OpenAccountRequest): AccountResponse {
        val accountId = openAccount.execute(request.ownerId, request.initialBalanceCents)
        return AccountResponse(accountId, request.initialBalanceCents)
    }
}

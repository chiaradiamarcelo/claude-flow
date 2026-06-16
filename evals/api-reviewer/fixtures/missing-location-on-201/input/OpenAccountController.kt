package banking.api

import banking.api.dto.OpenAccountRequest
import banking.api.dto.AccountResponse
import banking.application.OpenAccountUseCase
import org.springframework.http.HttpStatus
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.ResponseStatus
import org.springframework.web.bind.annotation.RestController

@RestController
class OpenAccountController(
    private val openAccount: OpenAccountUseCase,
) {

    @PostMapping("/accounts")
    @ResponseStatus(HttpStatus.CREATED)
    fun open(@RequestBody request: OpenAccountRequest): AccountResponse {
        val accountId = openAccount.execute(request.ownerId, request.initialBalanceCents)
        return AccountResponse(accountId, request.initialBalanceCents)
    }
}

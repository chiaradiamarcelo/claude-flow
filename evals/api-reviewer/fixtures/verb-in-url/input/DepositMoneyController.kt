package banking.api

import banking.api.dto.DepositRequest
import banking.api.dto.BalanceResponse
import banking.application.DepositMoneyUseCase
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RestController

@RestController
class DepositMoneyController(
    private val depositMoney: DepositMoneyUseCase,
) {

    @PostMapping("/accounts/{id}/depositMoney")
    fun deposit(
        @PathVariable id: String,
        @RequestBody request: DepositRequest,
    ): BalanceResponse =
        BalanceResponse(depositMoney.execute(id, request.amountCents))
}

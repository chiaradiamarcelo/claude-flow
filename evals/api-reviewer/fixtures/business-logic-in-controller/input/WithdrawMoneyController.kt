package banking.api

import banking.api.dto.WithdrawRequest
import banking.api.dto.BalanceResponse
import banking.application.WithdrawMoneyUseCase
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RestController

@RestController
class WithdrawMoneyController(
    private val withdrawMoney: WithdrawMoneyUseCase,
) {

    @PostMapping("/accounts/{id}/withdrawals")
    fun withdraw(
        @PathVariable id: String,
        @RequestBody request: WithdrawRequest,
    ): BalanceResponse {
        val balanceCents = withdrawMoney.balanceOf(id)
        if (request.amountCents > balanceCents) {
            throw IllegalStateException("insufficient funds")
        }
        val fee = if (request.amountCents > 500_000) request.amountCents / 100 else 0
        val newBalance = withdrawMoney.execute(id, request.amountCents + fee)
        return BalanceResponse(newBalance)
    }
}

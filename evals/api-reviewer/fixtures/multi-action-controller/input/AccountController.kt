package banking.api

import banking.api.dto.DepositRequest
import banking.api.dto.WithdrawRequest
import banking.api.dto.BalanceResponse
import banking.application.DepositMoneyUseCase
import banking.application.WithdrawMoneyUseCase
import banking.application.CloseAccountUseCase
import org.springframework.web.bind.annotation.DeleteMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RestController

@RestController
class AccountController(
    private val depositMoney: DepositMoneyUseCase,
    private val withdrawMoney: WithdrawMoneyUseCase,
    private val closeAccount: CloseAccountUseCase,
) {

    @PostMapping("/accounts/{id}/deposits")
    fun deposit(@PathVariable id: String, @RequestBody request: DepositRequest): BalanceResponse =
        BalanceResponse(depositMoney.execute(id, request.amountCents))

    @PostMapping("/accounts/{id}/withdrawals")
    fun withdraw(@PathVariable id: String, @RequestBody request: WithdrawRequest): BalanceResponse =
        BalanceResponse(withdrawMoney.execute(id, request.amountCents))

    @DeleteMapping("/accounts/{id}")
    fun close(@PathVariable id: String) {
        closeAccount.execute(id)
    }
}

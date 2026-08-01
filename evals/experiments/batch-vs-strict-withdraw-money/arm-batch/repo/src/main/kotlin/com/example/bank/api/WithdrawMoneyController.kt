package com.example.bank.api

import com.example.bank.api.dto.WithdrawalRequest
import com.example.bank.api.dto.WithdrawalResponse
import com.example.bank.application.WithdrawMoneyUseCase
import com.example.bank.domain.models.account.Account
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RestController

@RestController
class WithdrawMoneyController(
    private val withdrawMoney: WithdrawMoneyUseCase,
) {

    @PostMapping("/accounts/{accountId}/withdrawals")
    fun withdraw(
        @PathVariable accountId: String,
        @RequestBody request: WithdrawalRequest,
    ): WithdrawalResponse = toResponse(withdrawMoney.execute(accountId, request.amount))

    private fun toResponse(account: Account): WithdrawalResponse =
        WithdrawalResponse(account.accountId(), account.balance())
}

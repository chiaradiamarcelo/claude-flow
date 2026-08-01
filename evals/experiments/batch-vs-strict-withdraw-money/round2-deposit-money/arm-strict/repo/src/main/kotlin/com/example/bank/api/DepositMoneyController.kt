package com.example.bank.api

import com.example.bank.api.dto.DepositRequest
import com.example.bank.api.dto.DepositResponse
import com.example.bank.application.DepositMoneyUseCase
import com.example.bank.domain.models.account.Account
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestBody
import org.springframework.web.bind.annotation.RestController

@RestController
class DepositMoneyController(
    private val depositMoneyUseCase: DepositMoneyUseCase,
) {

    @PostMapping("/accounts/{accountId}/deposits")
    fun deposit(
        @PathVariable accountId: String,
        @RequestBody request: DepositRequest,
    ): DepositResponse = toResponse(depositMoneyUseCase.deposit(accountId, request.amount))

    private fun toResponse(account: Account): DepositResponse =
        DepositResponse(account.accountId, account.balance)
}

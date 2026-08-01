package com.example.bank.application

import com.example.bank.domain.models.account.Account
import com.example.bank.domain.models.account.AccountNotFoundException
import com.example.bank.domain.models.account.AccountRepository
import java.math.BigDecimal

class DepositMoneyUseCase(
    private val accountRepository: AccountRepository,
) {

    fun deposit(accountId: String, amount: BigDecimal): Account {
        val account = accountRepository.findById(accountId)
            ?: throw AccountNotFoundException(accountId)

        return accountRepository.save(account.deposit(amount))
    }
}

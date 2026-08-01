package com.example.bank.domain.models.account.fakes

import com.example.bank.domain.models.account.Account
import com.example.bank.domain.models.account.AccountRepository

class FakeAccountRepository : AccountRepository {

    private val accountsById = mutableMapOf<String, Account>()

    override fun save(account: Account) {
        accountsById[account.accountId()] = account
    }

    override fun findById(accountId: String): Account? = accountsById[accountId]
}

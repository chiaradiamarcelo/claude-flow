package com.example.bank.domain.models.account.fakes

import com.example.bank.domain.models.account.AccountRepository
import com.example.bank.domain.models.account.AccountRepositoryContract
import org.junit.jupiter.api.BeforeEach

class FakeAccountRepositoryTest : AccountRepositoryContract() {

    override lateinit var accountRepository: AccountRepository

    @BeforeEach
    fun setUp() {
        accountRepository = FakeAccountRepository()
    }
}

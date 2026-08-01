package com.example.bank.domain.models.account.fakes

import com.example.bank.domain.models.account.AccountRepository
import com.example.bank.domain.models.account.AccountRepositoryContractTest
import org.junit.jupiter.api.BeforeEach

class FakeAccountRepositoryTest : AccountRepositoryContractTest() {

    override lateinit var repository: AccountRepository

    @BeforeEach
    fun setUp() {
        repository = FakeAccountRepository()
    }
}

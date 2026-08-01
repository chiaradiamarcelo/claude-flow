package com.example.bank.infrastructure

import com.example.bank.domain.models.account.AccountRepository
import com.example.bank.domain.models.account.AccountRepositoryContract
import org.junit.jupiter.api.BeforeEach
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest

@DataJpaTest
class AccountRepositoryJpaAdapterTest : AccountRepositoryContract() {

    @Autowired
    private lateinit var accountJpaRepository: AccountJpaRepository

    override lateinit var accountRepository: AccountRepository

    @BeforeEach
    fun setUp() {
        accountJpaRepository.deleteAll()
        accountRepository = AccountRepositoryJpaAdapter(accountJpaRepository)
    }
}

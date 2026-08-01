package com.example.bank.infrastructure.config

import com.example.bank.application.DepositMoneyUseCase
import com.example.bank.domain.models.account.AccountRepository
import com.example.bank.infrastructure.AccountJpaRepository
import com.example.bank.infrastructure.AccountRepositoryJpaAdapter
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class AccountConfiguration {

    @Bean
    fun accountRepository(accountJpaRepository: AccountJpaRepository): AccountRepository =
        AccountRepositoryJpaAdapter(accountJpaRepository)

    @Bean
    fun depositMoneyUseCase(accountRepository: AccountRepository): DepositMoneyUseCase =
        DepositMoneyUseCase(accountRepository)
}

package com.example.bank.infrastructure.config

import com.example.bank.application.DepositMoneyUseCase
import com.example.bank.domain.models.account.AccountRepository
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class UseCaseConfiguration {

    @Bean
    fun depositMoneyUseCase(accounts: AccountRepository): DepositMoneyUseCase =
        DepositMoneyUseCase(accounts)
}

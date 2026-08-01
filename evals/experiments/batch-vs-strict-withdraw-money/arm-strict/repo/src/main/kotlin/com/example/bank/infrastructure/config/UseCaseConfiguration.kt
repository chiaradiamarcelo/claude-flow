package com.example.bank.infrastructure.config

import com.example.bank.application.WithdrawMoneyUseCase
import com.example.bank.domain.models.account.AccountRepository
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

@Configuration
class UseCaseConfiguration {

    @Bean
    fun withdrawMoneyUseCase(accountRepository: AccountRepository) = WithdrawMoneyUseCase(accountRepository)
}

class CreateOrderControllerIT {

    private lateinit var useCase: CreateOrder
    private lateinit var client: TestHttpClient

    @BeforeEach
    fun setUp() {
        useCase = mock(CreateOrder::class.java)
        client = TestHttpClient(OrderController(useCase))
    }

    @Test
    fun returns_201_when_the_order_is_created() {
        whenever(useCase.create(any())).thenReturn(OrderId("id_1"))

        val response = client.post("/orders", body = mapOf("amount" to 99.99, "currency" to "USD"))

        assertThat(response.status).isEqualTo(201)
        assertThat(response.header("Location")).isEqualTo("/orders/id_1")
    }
}

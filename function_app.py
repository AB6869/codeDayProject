import azure.functions as func
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# corefunctions 

@app.route(route="myTestFunctionHTTP")
def TestFunctionHTTP(req: func.HttpRequest) -> func.HttpResponse:
    from corefunctions.TestFunctions import test_function_HTTP
    return test_function_HTTP(req)


@app.function_name(name="myTestFunctionQueue")
@app.queue_trigger(arg_name="azqueue", queue_name="test-function",
                               connection="AzureWebJobsStorage") 
def TestFunctionQueue(azqueue: func.QueueMessage):
    from corefunctions.TestFunctions import test_function_queue
    test_function_queue(azqueue.get_body().decode('utf-8'))


@app.function_name(name="myTestFunctionTimer")
@app.timer_trigger(schedule="0 0 3 * * 6", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def TestFunctionTimer(myTimer: func.TimerRequest) -> None:
    from corefunctions.TestFunctions import test_function_timer
    test_function_timer()


@app.function_name(name="myTestFunctionSbQueue")
@app.service_bus_queue_trigger(arg_name="azservicebus", queue_name="local-test-perre",
                               connection="AzureServiceBus") 
def TestFunctionSbQueue(azservicebus: func.ServiceBusMessage):
    from corefunctions.TestFunctions import test_function_queue
    test_function_queue(azservicebus.get_body().decode('utf-8'))



# Standard function to keep messages in loop. Standard lenght of an untouched message i storage is 10 days.
@app.function_name(name="RetryAllPoison")
@app.timer_trigger(schedule="0 0 3 * * 6", arg_name="myTimer", run_on_startup=True,
              use_monitor=False) 
def RetryAllPoison(myTimer: func.TimerRequest) -> None:
    from _lib.queue_service import retry_all_msg_in_poison
    retry_all_msg_in_poison()








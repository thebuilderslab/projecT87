
#!/usr/bin/env python3
"""
Emergency Data Sync Fix
Resolves stale/cached data vs live data mismatches
"""

import json
import time
from web3 import Web3
from arbitrum_testnet_agent import ArbitrumTestnetAgent

def fix_data_sync():
    """Fix data synchronization issues"""
    print("🔧 EMERGENCY DATA SYNC FIX")
    print("=" * 50)
    
    try:
        # Initialize agent
        agent = ArbitrumTestnetAgent()
        agent.initialize_integrations()
        
        print(f"🔍 Checking live Aave data vs cached data...")
        
        # Get fresh live data directly from Aave contract
        pool_abi = [{
            "inputs": [{"name": "user", "type": "address"}],
            "name": "getUserAccountData",
            "outputs": [
                {"name": "totalCollateralBase", "type": "uint256"},
                {"name": "totalDebtBase", "type": "uint256"},
                {"name": "availableBorrowsBase", "type": "uint256"},
                {"name": "currentLiquidationThreshold", "type": "uint256"},
                {"name": "ltv", "type": "uint256"},
                {"name": "healthFactor", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function"
        }]
        
        pool_contract = agent.w3.eth.contract(
            address=agent.aave_pool_address,
            abi=pool_abi
        )
        
        account_data = pool_contract.functions.getUserAccountData(agent.address).call()
        
        live_collateral = account_data[0] / (10**8)
        live_debt = account_data[1] / (10**8)
        live_available = account_data[2] / (10**8)
        live_hf = account_data[5] / (10**18) if account_data[5] > 0 else float('inf')
        
        print(f"✅ LIVE AAVE DATA:")
        print(f"   Collateral: ${live_collateral:.2f}")
        print(f"   Debt: ${live_debt:.2f}")
        print(f"   Available Borrows: ${live_available:.2f}")
        print(f"   Health Factor: {live_hf:.3f}")
        
        # Force update baseline if we have good data
        if live_collateral > 50:
            agent.last_collateral_value_usd = live_collateral
            agent.baseline_initialized = True
            
            # Save to baseline file
            baseline_data = {
                'last_collateral_value_usd': live_collateral,
                'baseline_initialized': True,
                'timestamp': time.time(),
                'wallet_address': agent.address,
                'sync_method': 'emergency_data_sync_fix'
            }
            
            with open('agent_baseline.json', 'w') as f:
                json.dump(baseline_data, f, indent=2)
            
            print(f"✅ BASELINE SYNCHRONIZED: ${live_collateral:.2f}")
            print(f"🎯 Next trigger at: ${live_collateral + 12:.2f}")
            
            return True
        else:
            print(f"❌ Live data still shows insufficient collateral")
            return False
            
    except Exception as e:
        print(f"❌ Data sync fix failed: {e}")
        return False

if __name__ == "__main__":
    success = fix_data_sync()
    if success:
        print(f"\n✅ DATA SYNC FIXED!")
        print(f"System should now see live position correctly")
    else:
        print(f"\n❌ DATA SYNC FIX FAILED!")

# --- Merged from async_utils.py ---

def async_variant(normal_func):  # type: ignore
    def decorator(async_func):  # type: ignore
        pass_arg = _PassArg.from_obj(normal_func)
        need_eval_context = pass_arg is None

        if pass_arg is _PassArg.environment:

            def is_async(args: t.Any) -> bool:
                return t.cast(bool, args[0].is_async)

        else:

            def is_async(args: t.Any) -> bool:
                return t.cast(bool, args[0].environment.is_async)

        # Take the doc and annotations from the sync function, but the
        # name from the async function. Pallets-Sphinx-Themes
        # build_function_directive expects __wrapped__ to point to the
        # sync function.
        async_func_attrs = ("__module__", "__name__", "__qualname__")
        normal_func_attrs = tuple(set(WRAPPER_ASSIGNMENTS).difference(async_func_attrs))

        @wraps(normal_func, assigned=normal_func_attrs)
        @wraps(async_func, assigned=async_func_attrs, updated=())
        def wrapper(*args, **kwargs):  # type: ignore
            b = is_async(args)

            if need_eval_context:
                args = args[1:]

            if b:
                return async_func(*args, **kwargs)

            return normal_func(*args, **kwargs)

        if need_eval_context:
            wrapper = pass_eval_context(wrapper)

        wrapper.jinja_async_variant = True  # type: ignore[attr-defined]
        return wrapper

    return decorator

    def decorator(async_func):  # type: ignore
        pass_arg = _PassArg.from_obj(normal_func)
        need_eval_context = pass_arg is None

        if pass_arg is _PassArg.environment:

            def is_async(args: t.Any) -> bool:
                return t.cast(bool, args[0].is_async)

        else:

            def is_async(args: t.Any) -> bool:
                return t.cast(bool, args[0].environment.is_async)

        # Take the doc and annotations from the sync function, but the
        # name from the async function. Pallets-Sphinx-Themes
        # build_function_directive expects __wrapped__ to point to the
        # sync function.
        async_func_attrs = ("__module__", "__name__", "__qualname__")
        normal_func_attrs = tuple(set(WRAPPER_ASSIGNMENTS).difference(async_func_attrs))

        @wraps(normal_func, assigned=normal_func_attrs)
        @wraps(async_func, assigned=async_func_attrs, updated=())
        def wrapper(*args, **kwargs):  # type: ignore
            b = is_async(args)

            if need_eval_context:
                args = args[1:]

            if b:
                return async_func(*args, **kwargs)

            return normal_func(*args, **kwargs)

        if need_eval_context:
            wrapper = pass_eval_context(wrapper)

        wrapper.jinja_async_variant = True  # type: ignore[attr-defined]
        return wrapper

        def wrapper(*args, **kwargs):  # type: ignore
            b = is_async(args)

            if need_eval_context:
                args = args[1:]

            if b:
                return async_func(*args, **kwargs)

            return normal_func(*args, **kwargs)

            def is_async(args: t.Any) -> bool:
                return t.cast(bool, args[0].is_async)

            def is_async(args: t.Any) -> bool:
                return t.cast(bool, args[0].environment.is_async)
# --- Merged from async_timeout.py ---

def timeout(delay: Optional[float]) -> "Timeout":
    """timeout context manager.

    Useful in cases when you want to apply timeout logic around block
    of code or in cases when asyncio.wait_for is not suitable. For example:

    >>> async with timeout(0.001):
    ...     async with aiohttp.get('https://github.com') as r:
    ...         await r.text()


    delay - value in seconds or None to disable timeout logic
    """
    loop = asyncio.get_running_loop()
    if delay is not None:
        deadline = loop.time() + delay  # type: Optional[float]
    else:
        deadline = None
    return Timeout(deadline, loop)

def timeout_at(deadline: Optional[float]) -> "Timeout":
    """Schedule the timeout at absolute time.

    deadline argument points on the time in the same clock system
    as loop.time().

    Please note: it is not POSIX time but a time with
    undefined starting base, e.g. the time of the system power on.

    >>> async with timeout_at(loop.time() + 10):
    ...     async with aiohttp.get('https://github.com') as r:
    ...         await r.text()


    """
    loop = asyncio.get_running_loop()
    return Timeout(deadline, loop)

class _State(enum.Enum):
    INIT = "INIT"
    ENTER = "ENTER"
    TIMEOUT = "TIMEOUT"
    EXIT = "EXIT"

class Timeout:
    # Internal class, please don't instantiate it directly
    # Use timeout() and timeout_at() public factories instead.
    #
    # Implementation note: `async with timeout()` is preferred
    # over `with timeout()`.
    # While technically the Timeout class implementation
    # doesn't need to be async at all,
    # the `async with` statement explicitly points that
    # the context manager should be used from async function context.
    #
    # This design allows to avoid many silly misusages.
    #
    # TimeoutError is raised immediately when scheduled
    # if the deadline is passed.
    # The purpose is to time out as soon as possible
    # without waiting for the next await expression.

    __slots__ = ("_deadline", "_loop", "_state", "_timeout_handler", "_task")

    def __init__(
        self, deadline: Optional[float], loop: asyncio.AbstractEventLoop
    ) -> None:
        self._loop = loop
        self._state = _State.INIT

        self._task: Optional["asyncio.Task[object]"] = None
        self._timeout_handler = None  # type: Optional[asyncio.Handle]
        if deadline is None:
            self._deadline = None  # type: Optional[float]
        else:
            self.update(deadline)

    def __enter__(self) -> "Timeout":
        warnings.warn(
            "with timeout() is deprecated, use async with timeout() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        self._do_enter()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        self._do_exit(exc_type)
        return None

    async def __aenter__(self) -> "Timeout":
        self._do_enter()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        self._do_exit(exc_type)
        return None

    @property
    def expired(self) -> bool:
        """Is timeout expired during execution?"""
        return self._state == _State.TIMEOUT

    @property
    def deadline(self) -> Optional[float]:
        return self._deadline

    def reject(self) -> None:
        """Reject scheduled timeout if any."""
        # cancel is maybe better name but
        # task.cancel() raises CancelledError in asyncio world.
        if self._state not in (_State.INIT, _State.ENTER):
            raise RuntimeError(f"invalid state {self._state.value}")
        self._reject()

    def _reject(self) -> None:
        self._task = None
        if self._timeout_handler is not None:
            self._timeout_handler.cancel()
            self._timeout_handler = None

    def shift(self, delay: float) -> None:
        """Advance timeout on delay seconds.

        The delay can be negative.

        Raise RuntimeError if shift is called when deadline is not scheduled
        """
        deadline = self._deadline
        if deadline is None:
            raise RuntimeError("cannot shift timeout if deadline is not scheduled")
        self.update(deadline + delay)

    def update(self, deadline: float) -> None:
        """Set deadline to absolute value.

        deadline argument points on the time in the same clock system
        as loop.time().

        If new deadline is in the past the timeout is raised immediately.

        Please note: it is not POSIX time but a time with
        undefined starting base, e.g. the time of the system power on.
        """
        if self._state == _State.EXIT:
            raise RuntimeError("cannot reschedule after exit from context manager")
        if self._state == _State.TIMEOUT:
            raise RuntimeError("cannot reschedule expired timeout")
        if self._timeout_handler is not None:
            self._timeout_handler.cancel()
        self._deadline = deadline
        if self._state != _State.INIT:
            self._reschedule()

    def _reschedule(self) -> None:
        assert self._state == _State.ENTER
        deadline = self._deadline
        if deadline is None:
            return

        now = self._loop.time()
        if self._timeout_handler is not None:
            self._timeout_handler.cancel()

        self._task = asyncio.current_task()
        if deadline <= now:
            self._timeout_handler = self._loop.call_soon(self._on_timeout)
        else:
            self._timeout_handler = self._loop.call_at(deadline, self._on_timeout)

    def _do_enter(self) -> None:
        if self._state != _State.INIT:
            raise RuntimeError(f"invalid state {self._state.value}")
        self._state = _State.ENTER
        self._reschedule()

    def _do_exit(self, exc_type: Optional[Type[BaseException]]) -> None:
        if exc_type is asyncio.CancelledError and self._state == _State.TIMEOUT:
            assert self._task is not None
            _uncancel_task(self._task)
            self._timeout_handler = None
            self._task = None
            raise asyncio.TimeoutError
        # timeout has not expired
        self._state = _State.EXIT
        self._reject()
        return None

    def _on_timeout(self) -> None:
        assert self._task is not None
        self._task.cancel()
        self._state = _State.TIMEOUT
        # drop the reference early
        self._timeout_handler = None

    def final(f):
        """This decorator can be used to indicate to type checkers that
        the decorated method cannot be overridden, and decorated class
        cannot be subclassed. For example:

            class Base:
                @final
                def done(self) -> None:
                    ...
            class Sub(Base):
                def done(self) -> None:  # Error reported by type checker
                    ...
            @final
            class Leaf:
                ...
            class Other(Leaf):  # Error reported by type checker
                ...

        There is no runtime checking of these properties. The decorator
        sets the ``__final__`` attribute to ``True`` on the decorated object
        to allow runtime introspection.
        """
        try:
            f.__final__ = True
        except (AttributeError, TypeError):
            # Skip the attribute silently if it is not writable.
            # AttributeError happens if the object has __slots__ or a
            # read-only property, TypeError if it's a builtin class.
            pass
        return f

    def _uncancel_task(task: "asyncio.Task[object]") -> None:
        task.uncancel()

    def _uncancel_task(task: "asyncio.Task[object]") -> None:
        pass

    def __init__(
        self, deadline: Optional[float], loop: asyncio.AbstractEventLoop
    ) -> None:
        self._loop = loop
        self._state = _State.INIT

        self._task: Optional["asyncio.Task[object]"] = None
        self._timeout_handler = None  # type: Optional[asyncio.Handle]
        if deadline is None:
            self._deadline = None  # type: Optional[float]
        else:
            self.update(deadline)

    def __enter__(self) -> "Timeout":
        warnings.warn(
            "with timeout() is deprecated, use async with timeout() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        self._do_enter()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        self._do_exit(exc_type)
        return None

    def expired(self) -> bool:
        """Is timeout expired during execution?"""
        return self._state == _State.TIMEOUT

    def deadline(self) -> Optional[float]:
        return self._deadline

    def reject(self) -> None:
        """Reject scheduled timeout if any."""
        # cancel is maybe better name but
        # task.cancel() raises CancelledError in asyncio world.
        if self._state not in (_State.INIT, _State.ENTER):
            raise RuntimeError(f"invalid state {self._state.value}")
        self._reject()

    def _reject(self) -> None:
        self._task = None
        if self._timeout_handler is not None:
            self._timeout_handler.cancel()
            self._timeout_handler = None

    def shift(self, delay: float) -> None:
        """Advance timeout on delay seconds.

        The delay can be negative.

        Raise RuntimeError if shift is called when deadline is not scheduled
        """
        deadline = self._deadline
        if deadline is None:
            raise RuntimeError("cannot shift timeout if deadline is not scheduled")
        self.update(deadline + delay)

    def update(self, deadline: float) -> None:
        """Set deadline to absolute value.

        deadline argument points on the time in the same clock system
        as loop.time().

        If new deadline is in the past the timeout is raised immediately.

        Please note: it is not POSIX time but a time with
        undefined starting base, e.g. the time of the system power on.
        """
        if self._state == _State.EXIT:
            raise RuntimeError("cannot reschedule after exit from context manager")
        if self._state == _State.TIMEOUT:
            raise RuntimeError("cannot reschedule expired timeout")
        if self._timeout_handler is not None:
            self._timeout_handler.cancel()
        self._deadline = deadline
        if self._state != _State.INIT:
            self._reschedule()

    def _reschedule(self) -> None:
        assert self._state == _State.ENTER
        deadline = self._deadline
        if deadline is None:
            return

        now = self._loop.time()
        if self._timeout_handler is not None:
            self._timeout_handler.cancel()

        self._task = asyncio.current_task()
        if deadline <= now:
            self._timeout_handler = self._loop.call_soon(self._on_timeout)
        else:
            self._timeout_handler = self._loop.call_at(deadline, self._on_timeout)

    def _do_enter(self) -> None:
        if self._state != _State.INIT:
            raise RuntimeError(f"invalid state {self._state.value}")
        self._state = _State.ENTER
        self._reschedule()

    def _do_exit(self, exc_type: Optional[Type[BaseException]]) -> None:
        if exc_type is asyncio.CancelledError and self._state == _State.TIMEOUT:
            assert self._task is not None
            _uncancel_task(self._task)
            self._timeout_handler = None
            self._task = None
            raise asyncio.TimeoutError
        # timeout has not expired
        self._state = _State.EXIT
        self._reject()
        return None

    def _on_timeout(self) -> None:
        assert self._task is not None
        self._task.cancel()
        self._state = _State.TIMEOUT
        # drop the reference early
        self._timeout_handler = None
# --- Merged from async_ens.py ---

class AsyncENS(BaseENS):
    """
    Quick access to common Ethereum Name Service functions,
    like getting the address for a name.

    Unless otherwise specified, all addresses are assumed to be a `str` in
    `checksum format <https://github.com/ethereum/EIPs/blob/master/EIPS/eip-155.md>`_,
    like: ``"0x314159265dD8dbb310642f98f50C066173C1259b"``
    """

    # mypy types
    w3: "AsyncWeb3"

    def __init__(
        self,
        provider: "AsyncBaseProvider" = cast("AsyncBaseProvider", default),
        addr: ChecksumAddress = None,
        middlewares: Optional[Sequence[Tuple["AsyncMiddleware", str]]] = None,
    ) -> None:
        """
        :param provider: a single provider used to connect to Ethereum
        :type provider: instance of `web3.providers.base.BaseProvider`
        :param hex-string addr: the address of the ENS registry on-chain.
            If not provided, ENS.py will default to the mainnet ENS registry address.
        """
        self.w3 = init_async_web3(provider, middlewares)

        ens_addr = addr if addr else ENS_MAINNET_ADDR
        self.ens = self.w3.eth.contract(abi=abis.ENS, address=ens_addr)
        self._resolver_contract = self.w3.eth.contract(
            abi=abis.PUBLIC_RESOLVER_2_EXTENDED
        )
        self._reverse_resolver_contract = self.w3.eth.contract(
            abi=abis.REVERSE_RESOLVER
        )

    @classmethod
    def from_web3(cls, w3: "AsyncWeb3", addr: ChecksumAddress = None) -> "AsyncENS":
        """
        Generate an AsyncENS instance with web3

        :param `web3.Web3` w3: to infer connection information
        :param hex-string addr: the address of the ENS registry on-chain. If not
            provided, defaults to the mainnet ENS registry address.
        """
        provider = w3.manager.provider
        middlewares = w3.middleware_onion.middlewares
        ns = cls(
            cast("AsyncBaseProvider", provider), addr=addr, middlewares=middlewares
        )

        # inherit strict bytes checking from w3 instance
        ns.strict_bytes_type_checking = w3.strict_bytes_type_checking

        return ns

    async def address(
        self,
        name: str,
        coin_type: Optional[int] = None,
    ) -> Optional[ChecksumAddress]:
        """
        Look up the Ethereum address that `name` currently points to.

        :param str name: an ENS name to look up
        :param int coin_type: if provided, look up the address for this coin type
        :raises InvalidName: if `name` has invalid syntax
        """
        r = await self.resolver(name)
        if coin_type is None:
            # don't validate `addr(bytes32)` interface id since extended resolvers
            # can implement a "resolve" function as of ENSIP-10
            return cast(ChecksumAddress, await self._resolve(name, "addr"))
        else:
            await _async_validate_resolver_and_interface_id(
                name, r, ENS_MULTICHAIN_ADDRESS_INTERFACE_ID, "addr(bytes32,uint256)"
            )
            node = raw_name_to_hash(name)
            address_as_bytes = await r.caller.addr(node, coin_type)
            if is_none_or_zero_address(address_as_bytes):
                return None
            return to_checksum_address(address_as_bytes)

    async def setup_address(
        self,
        name: str,
        address: Union[Address, ChecksumAddress, HexAddress] = cast(
            ChecksumAddress, default
        ),
        coin_type: Optional[int] = None,
        transact: Optional["TxParams"] = None,
    ) -> Optional[HexBytes]:
        """
        Set up the name to point to the supplied address.
        The sender of the transaction must own the name, or
        its parent name.

        Example: If the caller owns ``parentname.eth`` with no subdomains
        and calls this method with ``sub.parentname.eth``,
        then ``sub`` will be created as part of this call.

        :param str name: ENS name to set up
        :param str address: name will point to this address, in checksum format.
            If ``None``, erase the record. If not specified, name will point
            to the owner's address.
        :param int coin_type: if provided, set up the address for this coin type
        :param dict transact: the transaction configuration, like in
            :meth:`~web3.eth.Eth.send_transaction`
        :raises InvalidName: if ``name`` has invalid syntax
        :raises UnauthorizedError: if ``'from'`` in `transact` does not own `name`
        """
        if not transact:
            transact = {}
        transact = deepcopy(transact)
        owner = await self.setup_owner(name, transact=transact)
        await self._assert_control(owner, name)
        if is_none_or_zero_address(address):
            address = None
        elif address is default:
            address = owner
        elif is_binary_address(address):
            address = to_checksum_address(cast(str, address))
        elif not is_checksum_address(address):
            raise ValueError("You must supply the address in checksum format")
        if await self.address(name) == address:
            return None
        if address is None:
            address = EMPTY_ADDR_HEX
        transact["from"] = owner

        resolver: "AsyncContract" = await self._set_resolver(name, transact=transact)
        node = raw_name_to_hash(name)

        if coin_type is None:
            return await resolver.functions.setAddr(node, address).transact(transact)
        else:
            return await resolver.functions.setAddr(node, coin_type, address).transact(
                transact
            )

    async def name(self, address: ChecksumAddress) -> Optional[str]:
        """
        Look up the name that the address points to, using a
        reverse lookup. Reverse lookup is opt-in for name owners.

        :param address:
        :type address: hex-string
        """
        reversed_domain = address_to_reverse_domain(address)
        name = await self._resolve(reversed_domain, fn_name="name")

        # To be absolutely certain of the name, via reverse resolution,
        # the address must match in the forward resolution
        return (
            name if to_checksum_address(address) == await self.address(name) else None
        )

    async def setup_name(
        self,
        name: str,
        address: Optional[ChecksumAddress] = None,
        transact: Optional["TxParams"] = None,
    ) -> HexBytes:
        """
        Set up the address for reverse lookup, aka "caller ID".
        After successful setup, the method :meth:`~ens.ENS.name` will return
        `name` when supplied with `address`.

        :param str name: ENS name that address will point to
        :param str address: address to set up, in checksum format
        :param dict transact: the transaction configuration, like in
            :meth:`~web3.eth.send_transaction`
        :raises AddressMismatch: if the name does not already point to the address
        :raises InvalidName: if `name` has invalid syntax
        :raises UnauthorizedError: if ``'from'`` in `transact` does not own `name`
        :raises UnownedName: if no one owns `name`
        """
        if not transact:
            transact = {}
        transact = deepcopy(transact)
        if not name:
            await self._assert_control(address, "the reverse record")
            return await self._setup_reverse(None, address, transact=transact)
        else:
            resolved = await self.address(name)
            if is_none_or_zero_address(address):
                address = resolved
            elif resolved and address != resolved and resolved != EMPTY_ADDR_HEX:
                raise AddressMismatch(
                    f"Could not set address {address!r} to point to name, "
                    f"because the name resolves to {resolved!r}. "
                    "To change the name for an existing address, call "
                    "setup_address() first."
                )
            if is_none_or_zero_address(address):
                address = await self.owner(name)
            if is_none_or_zero_address(address):
                raise UnownedName("claim subdomain using setup_address() first")
            if is_binary_address(address):
                address = to_checksum_address(address)
            if not is_checksum_address(address):
                raise ValueError("You must supply the address in checksum format")
            await self._assert_control(address, name)
            if not resolved:
                await self.setup_address(name, address, transact=transact)
            return await self._setup_reverse(name, address, transact=transact)

    async def owner(self, name: str) -> ChecksumAddress:
        """
        Get the owner of a name. Note that this may be different from the
        deed holder in the '.eth' registrar. Learn more about the difference
        between deed and name ownership in the ENS `Managing Ownership docs
        <http://docs.ens.domains/en/latest/userguide.html#managing-ownership>`_

        :param str name: ENS name to look up
        :return: owner address
        :rtype: str
        """
        node = raw_name_to_hash(name)
        return await self.ens.caller.owner(node)

    async def setup_owner(
        self,
        name: str,
        new_owner: ChecksumAddress = cast(ChecksumAddress, default),
        transact: Optional["TxParams"] = None,
    ) -> Optional[ChecksumAddress]:
        """
        Set the owner of the supplied name to `new_owner`.

        For typical scenarios, you'll never need to call this method directly,
        simply call :meth:`setup_name` or :meth:`setup_address`. This method does *not*
        set up the name to point to an address.

        If `new_owner` is not supplied, then this will assume you
        want the same owner as the parent domain.

        If the caller owns ``parentname.eth`` with no subdomains
        and calls this method with ``sub.parentname.eth``,
        then ``sub`` will be created as part of this call.

        :param str name: ENS name to set up
        :param new_owner: account that will own `name`. If ``None``,
            set owner to empty addr.  If not specified, name will point
            to the parent domain owner's address.
        :param dict transact: the transaction configuration, like in
            :meth:`~web3.eth.Eth.send_transaction`
        :raises InvalidName: if `name` has invalid syntax
        :raises UnauthorizedError: if ``'from'`` in `transact` does not own `name`
        :returns: the new owner's address
        """
        if not transact:
            transact = {}
        transact = deepcopy(transact)
        (super_owner, unowned, owned) = await self._first_owner(name)
        if new_owner is default:
            new_owner = super_owner
        elif not new_owner:
            new_owner = ChecksumAddress(EMPTY_ADDR_HEX)
        else:
            new_owner = to_checksum_address(new_owner)
        current_owner = await self.owner(name)
        if new_owner == EMPTY_ADDR_HEX and not current_owner:
            return None
        elif current_owner == new_owner:
            return current_owner
        else:
            await self._assert_control(super_owner, name, owned)
            await self._claim_ownership(
                new_owner, unowned, owned, super_owner, transact=transact
            )
            return new_owner

    async def resolver(self, name: str) -> Optional["AsyncContract"]:
        """
        Get the resolver for an ENS name.

        :param str name: The ENS name
        """
        normal_name = normalize_name(name)
        resolver = await self._get_resolver(normal_name)
        return resolver[0]

    async def reverser(
        self, target_address: ChecksumAddress
    ) -> Optional["AsyncContract"]:
        reversed_domain = address_to_reverse_domain(target_address)
        return await self.resolver(reversed_domain)

    # -- text records -- #

    async def get_text(self, name: str, key: str) -> str:
        """
        Get the value of a text record by key from an ENS name.

        :param str name: ENS name to look up
        :param str key: ENS name's text record key
        :return: ENS name's text record value
        :rtype: str
        :raises UnsupportedFunction: If the resolver does not support
            the "0x59d1d43c" interface id
        :raises ResolverNotFound: If no resolver is found for the provided name
        """
        node = raw_name_to_hash(name)

        r = await self.resolver(name)
        await _async_validate_resolver_and_interface_id(
            name, r, ENS_TEXT_INTERFACE_ID, "text"
        )
        return await r.caller.text(node, key)

    async def set_text(
        self,
        name: str,
        key: str,
        value: str,
        transact: "TxParams" = None,
    ) -> HexBytes:
        """
        Set the value of a text record of an ENS name.

        :param str name: ENS name
        :param str key: The name of the attribute to set
        :param str value: Value to set the attribute to
        :param dict transact: The transaction configuration, like in
            :meth:`~web3.eth.Eth.send_transaction`
        :return: Transaction hash
        :rtype: HexBytes
        :raises UnsupportedFunction: If the resolver does not support
            the "0x59d1d43c" interface id
        :raises ResolverNotFound: If no resolver is found for the provided name
        """
        r = await self.resolver(name)
        await _async_validate_resolver_and_interface_id(
            name, r, ENS_TEXT_INTERFACE_ID, "setText"
        )
        node = raw_name_to_hash(name)

        return await self._set_property(
            name, r.functions.setText, (node, key, value), transact
        )

    # -- private methods -- #

    async def _get_resolver(
        self,
        normal_name: str,
        fn_name: str = "addr",
    ) -> Tuple[Optional["AsyncContract"], str]:
        current_name = normal_name

        # look for a resolver, starting at the full name and taking the
        # parent each time that no resolver is found
        while True:
            if is_empty_name(current_name):
                # if no resolver found across all iterations, current_name
                # will eventually be the empty string '' which returns here
                return None, current_name

            resolver_addr = await self.ens.caller.resolver(
                normal_name_to_hash(current_name)
            )
            if not is_none_or_zero_address(resolver_addr):
                # if resolver found, return it
                resolver = cast(
                    "AsyncContract", self._type_aware_resolver(resolver_addr, fn_name)
                )
                return resolver, current_name

            # set current_name to parent and try again
            current_name = self.parent(current_name)

    async def _set_resolver(
        self,
        name: str,
        resolver_addr: Optional[ChecksumAddress] = None,
        transact: Optional["TxParams"] = None,
    ) -> "AsyncContract":
        if not transact:
            transact = {}
        transact = deepcopy(transact)
        if is_none_or_zero_address(resolver_addr):
            resolver_addr = await self.address("resolver.eth")
        namehash = raw_name_to_hash(name)
        if await self.ens.caller.resolver(namehash) != resolver_addr:
            await self.ens.functions.setResolver(  # type: ignore
                namehash, resolver_addr
            ).transact(transact)
        return cast("AsyncContract", self._resolver_contract(address=resolver_addr))

    async def _resolve(
        self,
        name: str,
        fn_name: str = "addr",
    ) -> Optional[Union[ChecksumAddress, str]]:
        normal_name = normalize_name(name)

        resolver, current_name = await self._get_resolver(normal_name, fn_name)
        if not resolver:
            return None

        node = self.namehash(normal_name)

        # handle extended resolver case
        if await _async_resolver_supports_interface(
            resolver, ENS_EXTENDED_RESOLVER_INTERFACE_ID
        ):
            contract_func_with_args = (fn_name, [node])

            calldata = resolver.encodeABI(*contract_func_with_args)
            contract_call_result = await resolver.caller.resolve(
                ens_encode_name(normal_name),
                calldata,
            )
            result = self._decode_ensip10_resolve_data(
                contract_call_result, resolver, fn_name
            )
            return to_checksum_address(result) if is_address(result) else result
        elif normal_name == current_name:
            lookup_function = getattr(resolver.functions, fn_name)
            result = await lookup_function(node).call()
            if is_none_or_zero_address(result):
                return None
            return to_checksum_address(result) if is_address(result) else result
        return None

    async def _assert_control(
        self,
        account: ChecksumAddress,
        name: str,
        parent_owned: Optional[str] = None,
    ) -> None:
        if not address_in(account, await self.w3.eth.accounts):
            raise UnauthorizedError(
                f"in order to modify {name!r}, you must control account"
                f" {account!r}, which owns {parent_owned or name!r}"
            )

    async def _first_owner(
        self, name: str
    ) -> Tuple[Optional[ChecksumAddress], Sequence[str], str]:
        """
        Takes a name, and returns the owner of the deepest subdomain that has an owner

        :returns: (owner or None, list(unowned_subdomain_labels), first_owned_domain)
        """
        owner = None
        unowned = []
        pieces = normalize_name(name).split(".")
        while pieces and is_none_or_zero_address(owner):
            name = ".".join(pieces)
            owner = await self.owner(name)
            if is_none_or_zero_address(owner):
                unowned.append(pieces.pop(0))
        return (owner, unowned, name)

    async def _claim_ownership(
        self,
        owner: ChecksumAddress,
        unowned: Sequence[str],
        owned: str,
        old_owner: Optional[ChecksumAddress] = None,
        transact: Optional["TxParams"] = None,
    ) -> None:
        if not transact:
            transact = {}
        transact = deepcopy(transact)
        transact["from"] = old_owner or owner
        for label in reversed(unowned):
            await self.ens.functions.setSubnodeOwner(  # type: ignore
                raw_name_to_hash(owned),
                label_to_hash(label),
                owner,
            ).transact(transact)
            owned = f"{label}.{owned}"

    async def _setup_reverse(
        self,
        name: Optional[str],
        address: ChecksumAddress,
        transact: Optional["TxParams"] = None,
    ) -> HexBytes:
        name = normalize_name(name) if name else ""
        if not transact:
            transact = {}
        transact = deepcopy(transact)
        transact["from"] = address
        reverse_registrar = await self._reverse_registrar()
        return await reverse_registrar.functions.setName(name).transact(transact)

    async def _reverse_registrar(self) -> "AsyncContract":
        addr = await self.ens.caller.owner(
            normal_name_to_hash(REVERSE_REGISTRAR_DOMAIN)
        )
        return self.w3.eth.contract(address=addr, abi=abis.REVERSE_REGISTRAR)

    async def _set_property(
        self,
        name: str,
        func: "AsyncContractFunction",
        args: Sequence[Any],
        transact: "TxParams" = None,
    ) -> HexBytes:
        if not transact:
            transact = {}

        owner = await self.owner(name)
        transact_from_owner = merge({"from": owner}, transact)

        return await func(*args).transact(transact_from_owner)

    def from_web3(cls, w3: "AsyncWeb3", addr: ChecksumAddress = None) -> "AsyncENS":
        """
        Generate an AsyncENS instance with web3

        :param `web3.Web3` w3: to infer connection information
        :param hex-string addr: the address of the ENS registry on-chain. If not
            provided, defaults to the mainnet ENS registry address.
        """
        provider = w3.manager.provider
        middlewares = w3.middleware_onion.middlewares
        ns = cls(
            cast("AsyncBaseProvider", provider), addr=addr, middlewares=middlewares
        )

        # inherit strict bytes checking from w3 instance
        ns.strict_bytes_type_checking = w3.strict_bytes_type_checking

        return ns
# --- Merged from async_beacon.py ---

class AsyncBeacon:
    is_async = True

    def __init__(
        self,
        base_url: str,
        request_timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url
        self.request_timeout = request_timeout

    async def _async_make_get_request(self, endpoint_uri: str) -> Dict[str, Any]:
        uri = URI(self.base_url + endpoint_uri)
        return await async_json_make_get_request(uri, timeout=self.request_timeout)

    # [ BEACON endpoints ]

    # states

    async def get_genesis(self) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_GENESIS)

    async def get_hash_root(self, state_id: str = "head") -> Dict[str, Any]:
        return await self._async_make_get_request(GET_HASH_ROOT.format(state_id))

    async def get_fork_data(self, state_id: str = "head") -> Dict[str, Any]:
        return await self._async_make_get_request(GET_FORK_DATA.format(state_id))

    async def get_finality_checkpoint(self, state_id: str = "head") -> Dict[str, Any]:
        return await self._async_make_get_request(
            GET_FINALITY_CHECKPOINT.format(state_id)
        )

    async def get_validators(self, state_id: str = "head") -> Dict[str, Any]:
        return await self._async_make_get_request(GET_VALIDATORS.format(state_id))

    async def get_validator(
        self, validator_id: str, state_id: str = "head"
    ) -> Dict[str, Any]:
        return await self._async_make_get_request(
            GET_VALIDATOR.format(state_id, validator_id)
        )

    async def get_validator_balances(self, state_id: str = "head") -> Dict[str, Any]:
        return await self._async_make_get_request(
            GET_VALIDATOR_BALANCES.format(state_id)
        )

    async def get_epoch_committees(self, state_id: str = "head") -> Dict[str, Any]:
        return await self._async_make_get_request(GET_EPOCH_COMMITTEES.format(state_id))

    async def get_epoch_sync_committees(self, state_id: str = "head") -> Dict[str, Any]:
        return await self._async_make_get_request(
            GET_EPOCH_SYNC_COMMITTEES.format(state_id)
        )

    async def get_epoch_randao(self, state_id: str = "head") -> Dict[str, Any]:
        return await self._async_make_get_request(GET_EPOCH_RANDAO.format(state_id))

    # headers

    async def get_block_headers(self) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_BLOCK_HEADERS)

    async def get_block_header(self, block_id: str) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_BLOCK_HEADER.format(block_id))

    # block

    async def get_block(self, block_id: str) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_BLOCK.format(block_id))

    async def get_block_root(self, block_id: str) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_BLOCK_ROOT.format(block_id))

    async def get_block_attestations(self, block_id: str) -> Dict[str, Any]:
        return await self._async_make_get_request(
            GET_BLOCK_ATTESTATIONS.format(block_id)
        )

    async def get_blinded_blocks(self, block_id: str) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_BLINDED_BLOCKS.format(block_id))

    # rewards

    async def get_rewards(self, block_id: str) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_REWARDS.format(block_id))

    # light client (untested but follows spec)

    async def get_light_client_bootstrap_structure(
        self, block_root: HexStr
    ) -> Dict[str, Any]:
        return await self._async_make_get_request(
            GET_LIGHT_CLIENT_BOOTSTRAP_STRUCTURE.format(block_root)
        )

    async def get_light_client_updates(self) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_LIGHT_CLIENT_UPDATES)

    async def get_light_client_finality_update(self) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_LIGHT_CLIENT_FINALITY_UPDATE)

    async def get_light_client_optimistic_update(self) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_LIGHT_CLIENT_OPTIMISTIC_UPDATE)

    # pool

    async def get_attestations(self) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_ATTESTATIONS)

    async def get_attester_slashings(self) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_ATTESTER_SLASHINGS)

    async def get_proposer_slashings(self) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_PROPOSER_SLASHINGS)

    async def get_voluntary_exits(self) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_VOLUNTARY_EXITS)

    async def get_bls_to_execution_changes(self) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_BLS_TO_EXECUTION_CHANGES)

    # [ CONFIG endpoints ]

    async def get_fork_schedule(self) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_FORK_SCHEDULE)

    async def get_spec(self) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_SPEC)

    async def get_deposit_contract(self) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_DEPOSIT_CONTRACT)

    # [ DEBUG endpoints ]

    async def get_beacon_state(self, state_id: str = "head") -> Dict[str, Any]:
        return await self._async_make_get_request(GET_BEACON_STATE.format(state_id))

    async def get_beacon_heads(self) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_BEACON_HEADS)

    # [ NODE endpoints ]

    async def get_node_identity(self) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_NODE_IDENTITY)

    async def get_peers(self) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_PEERS)

    async def get_peer(self, peer_id: str) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_PEER.format(peer_id))

    async def get_health(self) -> int:
        url = URI(self.base_url + GET_HEALTH)
        response = await async_get_response_from_get_request(url)
        return response.status

    async def get_version(self) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_VERSION)

    async def get_syncing(self) -> Dict[str, Any]:
        return await self._async_make_get_request(GET_SYNCING)
# --- Merged from async_contract.py ---

class AsyncContractEvent(BaseContractEvent):
    # mypy types
    w3: "AsyncWeb3"

    @combomethod
    async def get_logs(
        self,
        argument_filters: Optional[Dict[str, Any]] = None,
        fromBlock: Optional[BlockIdentifier] = None,
        toBlock: Optional[BlockIdentifier] = None,
        block_hash: Optional[HexBytes] = None,
    ) -> Awaitable[Iterable[EventData]]:
        """Get events for this contract instance using eth_getLogs API.

        This is a stateless method, as opposed to createFilter.
        It can be safely called against nodes which do not provide
        eth_newFilter API, like Infura nodes.

        If there are many events,
        like ``Transfer`` events for a popular token,
        the Ethereum node might be overloaded and timeout
        on the underlying JSON-RPC call.

        Example - how to get all ERC-20 token transactions
        for the latest 10 blocks:

        .. code-block:: python

            from = max(mycontract.web3.eth.block_number - 10, 1)
            to = mycontract.web3.eth.block_number

            events = mycontract.events.Transfer.getLogs(fromBlock=from, toBlock=to)

            for e in events:
                print(e["args"]["from"],
                    e["args"]["to"],
                    e["args"]["value"])

        The returned processed log values will look like:

        .. code-block:: python

            (
                AttributeDict({
                 'args': AttributeDict({}),
                 'event': 'LogNoArguments',
                 'logIndex': 0,
                 'transactionIndex': 0,
                 'transactionHash': HexBytes('...'),
                 'address': '0xF2E246BB76DF876Cef8b38ae84130F4F55De395b',
                 'blockHash': HexBytes('...'),
                 'blockNumber': 3
                }),
                AttributeDict(...),
                ...
            )

        See also: :func:`web3.middleware.filter.local_filter_middleware`.

        :param argument_filters: Filter by argument values. Indexed arguments are
          filtered by the node while non-indexed arguments are filtered by the library.
        :param fromBlock: block number or "latest", defaults to "latest"
        :param toBlock: block number or "latest". Defaults to "latest"
        :param block_hash: block hash. Cannot be set at the
          same time as fromBlock or toBlock
        :yield: Tuple of :class:`AttributeDict` instances
        """
        event_abi = self._get_event_abi()

        # validate ``argument_filters`` if present
        if argument_filters is not None:
            event_arg_names = get_abi_input_names(event_abi)
            if not all(arg in event_arg_names for arg in argument_filters.keys()):
                raise Web3ValidationError(
                    "When filtering by argument names, all argument names must be "
                    "present in the contract's event ABI."
                )

        _filter_params = self._get_event_filter_params(
            event_abi, argument_filters, fromBlock, toBlock, block_hash
        )
        # call JSON-RPC API
        logs = await self.w3.eth.get_logs(_filter_params)

        # convert raw binary data to Python proxy objects as described by ABI:
        all_event_logs = tuple(
            get_event_data(self.w3.codec, event_abi, entry) for entry in logs
        )
        filtered_logs = self._process_get_logs_argument_filters(
            event_abi,
            all_event_logs,
            argument_filters,
        )
        return cast(Awaitable[Iterable[EventData]], filtered_logs)

    @combomethod
    async def create_filter(
        self,
        *,  # PEP 3102
        argument_filters: Optional[Dict[str, Any]] = None,
        fromBlock: Optional[BlockIdentifier] = None,
        toBlock: BlockIdentifier = "latest",
        address: Optional[ChecksumAddress] = None,
        topics: Optional[Sequence[Any]] = None,
    ) -> AsyncLogFilter:
        """
        Create filter object that tracks logs emitted by this contract event.
        """
        filter_builder = AsyncEventFilterBuilder(self._get_event_abi(), self.w3.codec)
        self._set_up_filter_builder(
            argument_filters,
            fromBlock,
            toBlock,
            address,
            topics,
            filter_builder,
        )
        log_filter = await filter_builder.deploy(self.w3)
        log_filter.log_entry_formatter = get_event_data(
            self.w3.codec, self._get_event_abi()
        )
        log_filter.builder = filter_builder

        return log_filter

    @combomethod
    def build_filter(self) -> AsyncEventFilterBuilder:
        builder = AsyncEventFilterBuilder(
            self._get_event_abi(),
            self.w3.codec,
            formatter=get_event_data(self.w3.codec, self._get_event_abi()),
        )
        builder.address = self.address
        return builder

class AsyncContractEvents(BaseContractEvents):
    def __init__(
        self, abi: ABI, w3: "AsyncWeb3", address: Optional[ChecksumAddress] = None
    ) -> None:
        super().__init__(abi, w3, AsyncContractEvent, address)

class AsyncContractFunction(BaseContractFunction):
    # mypy types
    w3: "AsyncWeb3"

    def __call__(self, *args: Any, **kwargs: Any) -> "AsyncContractFunction":
        clone = copy.copy(self)
        if args is None:
            clone.args = tuple()
        else:
            clone.args = args

        if kwargs is None:
            clone.kwargs = {}
        else:
            clone.kwargs = kwargs
        clone._set_function_info()
        return clone

    @classmethod
    def factory(cls, class_name: str, **kwargs: Any) -> Self:
        return PropertyCheckingFactory(class_name, (cls,), kwargs)(kwargs.get("abi"))

    async def call(
        self,
        transaction: Optional[TxParams] = None,
        block_identifier: BlockIdentifier = None,
        state_override: Optional[CallOverride] = None,
        ccip_read_enabled: Optional[bool] = None,
    ) -> Any:
        """
        Execute a contract function call using the `eth_call` interface.

        This method prepares a ``Caller`` object that exposes the contract
        functions and public variables as callable Python functions.

        Reading a public ``owner`` address variable example:

        .. code-block:: python

            ContractFactory = w3.eth.contract(
                abi=wallet_contract_definition["abi"]
            )

            # Not a real contract address
            contract = ContractFactory("0x2f70d3d26829e412A602E83FE8EeBF80255AEeA5")

            # Read "owner" public variable
            addr = contract.functions.owner().call()

        :param transaction: Dictionary of transaction info for web3 interface
        :param block_identifier TODO
        :param state_override TODO
        :param ccip_read_enabled TODO
        :return: ``Caller`` object that has contract public functions
            and variables exposed as Python methods
        """
        call_transaction = self._get_call_txparams(transaction)

        block_id = await async_parse_block_identifier(self.w3, block_identifier)

        return await async_call_contract_function(
            self.w3,
            self.address,
            self._return_data_normalizers,
            self.function_identifier,
            call_transaction,
            block_id,
            self.contract_abi,
            self.abi,
            state_override,
            ccip_read_enabled,
            self.decode_tuples,
            *self.args,
            **self.kwargs,
        )

    async def transact(self, transaction: Optional[TxParams] = None) -> HexBytes:
        setup_transaction = self._transact(transaction)
        return await async_transact_with_contract_function(
            self.address,
            self.w3,
            self.function_identifier,
            setup_transaction,
            self.contract_abi,
            self.abi,
            *self.args,
            **self.kwargs,
        )

    async def estimate_gas(
        self,
        transaction: Optional[TxParams] = None,
        block_identifier: Optional[BlockIdentifier] = None,
    ) -> int:
        setup_transaction = self._estimate_gas(transaction)
        return await async_estimate_gas_for_function(
            self.address,
            self.w3,
            self.function_identifier,
            setup_transaction,
            self.contract_abi,
            self.abi,
            block_identifier,
            *self.args,
            **self.kwargs,
        )

    async def build_transaction(
        self, transaction: Optional[TxParams] = None
    ) -> TxParams:
        built_transaction = self._build_transaction(transaction)
        return await async_build_transaction_for_function(
            self.address,
            self.w3,
            self.function_identifier,
            built_transaction,
            self.contract_abi,
            self.abi,
            *self.args,
            **self.kwargs,
        )

    @staticmethod
    def get_fallback_function(
        abi: ABI,
        async_w3: "AsyncWeb3",
        address: Optional[ChecksumAddress] = None,
    ) -> "AsyncContractFunction":
        if abi and fallback_func_abi_exists(abi):
            return AsyncContractFunction.factory(
                "fallback",
                w3=async_w3,
                contract_abi=abi,
                address=address,
                function_identifier=FallbackFn,
            )()
        return cast(AsyncContractFunction, NonExistentFallbackFunction())

    @staticmethod
    def get_receive_function(
        abi: ABI,
        async_w3: "AsyncWeb3",
        address: Optional[ChecksumAddress] = None,
    ) -> "AsyncContractFunction":
        if abi and receive_func_abi_exists(abi):
            return AsyncContractFunction.factory(
                "receive",
                w3=async_w3,
                contract_abi=abi,
                address=address,
                function_identifier=ReceiveFn,
            )()
        return cast(AsyncContractFunction, NonExistentReceiveFunction())

class AsyncContractFunctions(BaseContractFunctions):
    def __init__(
        self,
        abi: ABI,
        w3: "AsyncWeb3",
        address: Optional[ChecksumAddress] = None,
        decode_tuples: Optional[bool] = False,
    ) -> None:
        super().__init__(abi, w3, AsyncContractFunction, address, decode_tuples)

    def __getattr__(self, function_name: str) -> "AsyncContractFunction":
        if self.abi is None:
            raise NoABIFound(
                "There is no ABI found for this contract.",
            )
        if "_functions" not in self.__dict__:
            raise NoABIFunctionsFound(
                "The abi for this contract contains no function definitions. ",
                "Are you sure you provided the correct contract abi?",
            )
        elif function_name not in self.__dict__["_functions"]:
            raise ABIFunctionNotFound(
                f"The function '{function_name}' was not found in this contract's abi.",
                " Are you sure you provided the correct contract abi?",
            )
        else:
            return super().__getattribute__(function_name)

class AsyncContract(BaseContract):
    functions: AsyncContractFunctions = None
    caller: "AsyncContractCaller" = None

    # mypy types
    w3: "AsyncWeb3"

    #: Instance of :class:`ContractEvents` presenting available Event ABIs
    events: AsyncContractEvents = None

    def __init__(self, address: Optional[ChecksumAddress] = None) -> None:
        """Create a new smart contract proxy object.

        :param address: Contract address as 0x hex string"""

        if self.w3 is None:
            raise AttributeError(
                "The `Contract` class has not been initialized.  Please use the "
                "`web3.contract` interface to create your contract class."
            )

        if address:
            self.address = normalize_address_no_ens(address)

        if not self.address:
            raise TypeError(
                "The address argument is required to instantiate a contract."
            )
        self.functions = AsyncContractFunctions(
            self.abi, self.w3, self.address, decode_tuples=self.decode_tuples
        )
        self.caller = AsyncContractCaller(
            self.abi, self.w3, self.address, decode_tuples=self.decode_tuples
        )
        self.events = AsyncContractEvents(self.abi, self.w3, self.address)
        self.fallback = AsyncContract.get_fallback_function(
            self.abi, self.w3, AsyncContractFunction, self.address
        )
        self.receive = AsyncContract.get_receive_function(
            self.abi, self.w3, AsyncContractFunction, self.address
        )

    @classmethod
    def factory(
        cls, w3: "AsyncWeb3", class_name: Optional[str] = None, **kwargs: Any
    ) -> Type[Self]:
        kwargs["w3"] = w3

        normalizers = {
            "abi": normalize_abi,
            "address": normalize_address_no_ens,
            "bytecode": normalize_bytecode,
            "bytecode_runtime": normalize_bytecode,
        }

        contract = cast(
            Type[Self],
            PropertyCheckingFactory(
                class_name or cls.__name__,
                (cls,),
                kwargs,
                normalizers=normalizers,
            ),
        )
        contract.functions = AsyncContractFunctions(
            contract.abi, contract.w3, decode_tuples=contract.decode_tuples
        )
        contract.caller = AsyncContractCaller(
            contract.abi,
            contract.w3,
            contract.address,
            decode_tuples=contract.decode_tuples,
        )
        contract.events = AsyncContractEvents(contract.abi, contract.w3)
        contract.fallback = AsyncContract.get_fallback_function(
            contract.abi,
            contract.w3,
            AsyncContractFunction,
        )
        contract.receive = AsyncContract.get_receive_function(
            contract.abi,
            contract.w3,
            AsyncContractFunction,
        )
        return contract

    @classmethod
    def constructor(cls, *args: Any, **kwargs: Any) -> Self:
        """
        :param args: The contract constructor arguments as positional arguments
        :param kwargs: The contract constructor arguments as keyword arguments
        :return: a contract constructor object
        """
        if cls.bytecode is None:
            raise ValueError(
                "Cannot call constructor on a contract that does not have "
                "'bytecode' associated with it"
            )

        return AsyncContractConstructor(cls.w3, cls.abi, cls.bytecode, *args, **kwargs)

    @combomethod
    def find_functions_by_identifier(
        cls,
        contract_abi: ABI,
        w3: "AsyncWeb3",
        address: ChecksumAddress,
        callable_check: Callable[..., Any],
    ) -> List["AsyncContractFunction"]:
        return cast(
            List[AsyncContractFunction],
            find_functions_by_identifier(
                contract_abi, w3, address, callable_check, AsyncContractFunction
            ),
        )

    @combomethod
    def get_function_by_identifier(
        cls, fns: Sequence["AsyncContractFunction"], identifier: str
    ) -> "AsyncContractFunction":
        return get_function_by_identifier(fns, identifier)

class AsyncContractCaller(BaseContractCaller):
    # mypy types
    w3: "AsyncWeb3"

    def __init__(
        self,
        abi: ABI,
        w3: "AsyncWeb3",
        address: ChecksumAddress,
        transaction: Optional[TxParams] = None,
        block_identifier: BlockIdentifier = None,
        ccip_read_enabled: Optional[bool] = None,
        decode_tuples: Optional[bool] = False,
    ) -> None:
        super().__init__(abi, w3, address, decode_tuples=decode_tuples)

        if self.abi:
            if transaction is None:
                transaction = {}

            self._functions = filter_by_type("function", self.abi)
            for func in self._functions:
                fn = AsyncContractFunction.factory(
                    func["name"],
                    w3=w3,
                    contract_abi=self.abi,
                    address=self.address,
                    function_identifier=func["name"],
                    decode_tuples=decode_tuples,
                )

                # TODO: The no_extra_call method gets around the fact that we can't call
                #  the full async method from within a class's __init__ method. We need
                #  to see if there's a way to account for all desired elif cases.
                block_id = parse_block_identifier_no_extra_call(w3, block_identifier)
                caller_method = partial(
                    self.call_function,
                    fn,
                    transaction=transaction,
                    block_identifier=block_id,
                    ccip_read_enabled=ccip_read_enabled,
                )

                setattr(self, func["name"], caller_method)

    def __call__(
        self,
        transaction: Optional[TxParams] = None,
        block_identifier: BlockIdentifier = None,
        ccip_read_enabled: Optional[bool] = None,
    ) -> "AsyncContractCaller":
        if transaction is None:
            transaction = {}
        return type(self)(
            self.abi,
            self.w3,
            self.address,
            transaction=transaction,
            block_identifier=block_identifier,
            ccip_read_enabled=ccip_read_enabled,
            decode_tuples=self.decode_tuples,
        )

class AsyncContractConstructor(BaseContractConstructor):
    # mypy types
    w3: "AsyncWeb3"

    @combomethod
    async def transact(self, transaction: Optional[TxParams] = None) -> HexBytes:
        return await self.w3.eth.send_transaction(self._get_transaction(transaction))

    @combomethod
    async def build_transaction(
        self, transaction: Optional[TxParams] = None
    ) -> TxParams:
        """
        Build the transaction dictionary without sending
        """
        built_transaction = self._build_transaction(transaction)
        return await async_fill_transaction_defaults(self.w3, built_transaction)

    @combomethod
    async def estimate_gas(
        self,
        transaction: Optional[TxParams] = None,
        block_identifier: Optional[BlockIdentifier] = None,
    ) -> int:
        transaction = self._estimate_gas(transaction)

        return await self.w3.eth.estimate_gas(
            transaction, block_identifier=block_identifier
        )

    def build_filter(self) -> AsyncEventFilterBuilder:
        builder = AsyncEventFilterBuilder(
            self._get_event_abi(),
            self.w3.codec,
            formatter=get_event_data(self.w3.codec, self._get_event_abi()),
        )
        builder.address = self.address
        return builder

    def __call__(self, *args: Any, **kwargs: Any) -> "AsyncContractFunction":
        clone = copy.copy(self)
        if args is None:
            clone.args = tuple()
        else:
            clone.args = args

        if kwargs is None:
            clone.kwargs = {}
        else:
            clone.kwargs = kwargs
        clone._set_function_info()
        return clone

    def factory(cls, class_name: str, **kwargs: Any) -> Self:
        return PropertyCheckingFactory(class_name, (cls,), kwargs)(kwargs.get("abi"))

    def get_fallback_function(
        abi: ABI,
        async_w3: "AsyncWeb3",
        address: Optional[ChecksumAddress] = None,
    ) -> "AsyncContractFunction":
        if abi and fallback_func_abi_exists(abi):
            return AsyncContractFunction.factory(
                "fallback",
                w3=async_w3,
                contract_abi=abi,
                address=address,
                function_identifier=FallbackFn,
            )()
        return cast(AsyncContractFunction, NonExistentFallbackFunction())

    def get_receive_function(
        abi: ABI,
        async_w3: "AsyncWeb3",
        address: Optional[ChecksumAddress] = None,
    ) -> "AsyncContractFunction":
        if abi and receive_func_abi_exists(abi):
            return AsyncContractFunction.factory(
                "receive",
                w3=async_w3,
                contract_abi=abi,
                address=address,
                function_identifier=ReceiveFn,
            )()
        return cast(AsyncContractFunction, NonExistentReceiveFunction())

    def __getattr__(self, function_name: str) -> "AsyncContractFunction":
        if self.abi is None:
            raise NoABIFound(
                "There is no ABI found for this contract.",
            )
        if "_functions" not in self.__dict__:
            raise NoABIFunctionsFound(
                "The abi for this contract contains no function definitions. ",
                "Are you sure you provided the correct contract abi?",
            )
        elif function_name not in self.__dict__["_functions"]:
            raise ABIFunctionNotFound(
                f"The function '{function_name}' was not found in this contract's abi.",
                " Are you sure you provided the correct contract abi?",
            )
        else:
            return super().__getattribute__(function_name)

    def factory(
        cls, w3: "AsyncWeb3", class_name: Optional[str] = None, **kwargs: Any
    ) -> Type[Self]:
        kwargs["w3"] = w3

        normalizers = {
            "abi": normalize_abi,
            "address": normalize_address_no_ens,
            "bytecode": normalize_bytecode,
            "bytecode_runtime": normalize_bytecode,
        }

        contract = cast(
            Type[Self],
            PropertyCheckingFactory(
                class_name or cls.__name__,
                (cls,),
                kwargs,
                normalizers=normalizers,
            ),
        )
        contract.functions = AsyncContractFunctions(
            contract.abi, contract.w3, decode_tuples=contract.decode_tuples
        )
        contract.caller = AsyncContractCaller(
            contract.abi,
            contract.w3,
            contract.address,
            decode_tuples=contract.decode_tuples,
        )
        contract.events = AsyncContractEvents(contract.abi, contract.w3)
        contract.fallback = AsyncContract.get_fallback_function(
            contract.abi,
            contract.w3,
            AsyncContractFunction,
        )
        contract.receive = AsyncContract.get_receive_function(
            contract.abi,
            contract.w3,
            AsyncContractFunction,
        )
        return contract

    def constructor(cls, *args: Any, **kwargs: Any) -> Self:
        """
        :param args: The contract constructor arguments as positional arguments
        :param kwargs: The contract constructor arguments as keyword arguments
        :return: a contract constructor object
        """
        if cls.bytecode is None:
            raise ValueError(
                "Cannot call constructor on a contract that does not have "
                "'bytecode' associated with it"
            )

        return AsyncContractConstructor(cls.w3, cls.abi, cls.bytecode, *args, **kwargs)

    def find_functions_by_identifier(
        cls,
        contract_abi: ABI,
        w3: "AsyncWeb3",
        address: ChecksumAddress,
        callable_check: Callable[..., Any],
    ) -> List["AsyncContractFunction"]:
        return cast(
            List[AsyncContractFunction],
            find_functions_by_identifier(
                contract_abi, w3, address, callable_check, AsyncContractFunction
            ),
        )

    def get_function_by_identifier(
        cls, fns: Sequence["AsyncContractFunction"], identifier: str
    ) -> "AsyncContractFunction":
        return get_function_by_identifier(fns, identifier)

    def __call__(
        self,
        transaction: Optional[TxParams] = None,
        block_identifier: BlockIdentifier = None,
        ccip_read_enabled: Optional[bool] = None,
    ) -> "AsyncContractCaller":
        if transaction is None:
            transaction = {}
        return type(self)(
            self.abi,
            self.w3,
            self.address,
            transaction=transaction,
            block_identifier=block_identifier,
            ccip_read_enabled=ccip_read_enabled,
            decode_tuples=self.decode_tuples,
        )
# --- Merged from async_eth.py ---

class AsyncEth(BaseEth):
    # mypy types
    w3: "AsyncWeb3"

    is_async = True

    _default_contract_factory: Type[Union[AsyncContract, AsyncContractCaller]] = (
        AsyncContract
    )

    # eth_accounts

    _accounts: Method[Callable[[], Awaitable[Tuple[ChecksumAddress]]]] = Method(
        RPC.eth_accounts,
        is_property=True,
    )

    @property
    async def accounts(self) -> Tuple[ChecksumAddress]:
        return await self._accounts()

    # eth_hashrate

    _hashrate: Method[Callable[[], Awaitable[int]]] = Method(
        RPC.eth_hashrate,
        is_property=True,
    )

    @property
    async def hashrate(self) -> int:
        return await self._hashrate()

    # eth_blockNumber

    get_block_number: Method[Callable[[], Awaitable[BlockNumber]]] = Method(
        RPC.eth_blockNumber,
        is_property=True,
    )

    @property
    async def block_number(self) -> BlockNumber:
        return await self.get_block_number()

    # eth_chainId

    _chain_id: Method[Callable[[], Awaitable[int]]] = Method(
        RPC.eth_chainId,
        is_property=True,
    )

    @property
    async def chain_id(self) -> int:
        return await self._chain_id()

    # eth_coinbase

    _coinbase: Method[Callable[[], Awaitable[ChecksumAddress]]] = Method(
        RPC.eth_coinbase,
        is_property=True,
    )

    @property
    async def coinbase(self) -> ChecksumAddress:
        return await self._coinbase()

    # eth_gasPrice

    _gas_price: Method[Callable[[], Awaitable[Wei]]] = Method(
        RPC.eth_gasPrice,
        is_property=True,
    )

    @property
    async def gas_price(self) -> Wei:
        return await self._gas_price()

    # eth_maxPriorityFeePerGas

    _max_priority_fee: Method[Callable[[], Awaitable[Wei]]] = Method(
        RPC.eth_maxPriorityFeePerGas,
        is_property=True,
    )

    @property
    async def max_priority_fee(self) -> Wei:
        """
        Try to use eth_maxPriorityFeePerGas but, since this is not part
        of the spec and is only supported by some clients, fall back to
        an eth_feeHistory calculation with min and max caps.
        """
        try:
            return await self._max_priority_fee()
        except (ValueError, MethodUnavailable):
            warnings.warn(
                "There was an issue with the method eth_maxPriorityFeePerGas. "
                "Calculating using eth_feeHistory."
            )
            return await async_fee_history_priority_fee(self)

    # eth_mining

    _mining: Method[Callable[[], Awaitable[bool]]] = Method(
        RPC.eth_mining,
        is_property=True,
    )

    @property
    async def mining(self) -> bool:
        return await self._mining()

    # eth_syncing

    _syncing: Method[Callable[[], Awaitable[Union[SyncStatus, bool]]]] = Method(
        RPC.eth_syncing,
        is_property=True,
    )

    @property
    async def syncing(self) -> Union[SyncStatus, bool]:
        return await self._syncing()

    # eth_feeHistory

    _fee_history: Method[
        Callable[
            [int, Union[BlockParams, BlockNumber], Optional[List[float]]],
            Awaitable[FeeHistory],
        ]
    ] = Method(RPC.eth_feeHistory, mungers=[default_root_munger])

    async def fee_history(
        self,
        block_count: int,
        newest_block: Union[BlockParams, BlockNumber],
        reward_percentiles: Optional[List[float]] = None,
    ) -> FeeHistory:
        reward_percentiles = reward_percentiles or []
        return await self._fee_history(block_count, newest_block, reward_percentiles)

    # eth_call

    _call: Method[
        Callable[
            [
                TxParams,
                Optional[BlockIdentifier],
                Optional[CallOverride],
            ],
            Awaitable[HexBytes],
        ]
    ] = Method(RPC.eth_call, mungers=[BaseEth.call_munger])

    async def call(
        self,
        transaction: TxParams,
        block_identifier: Optional[BlockIdentifier] = None,
        state_override: Optional[CallOverride] = None,
        ccip_read_enabled: Optional[bool] = None,
    ) -> HexBytes:
        ccip_read_enabled_on_provider = self.w3.provider.global_ccip_read_enabled
        if (
            # default conditions:
            ccip_read_enabled_on_provider
            and ccip_read_enabled is not False
            # explicit call flag overrides provider flag,
            # enabling ccip read for specific calls:
            or not ccip_read_enabled_on_provider
            and ccip_read_enabled is True
        ):
            return await self._durin_call(transaction, block_identifier, state_override)

        return await self._call(transaction, block_identifier, state_override)

    async def _durin_call(
        self,
        transaction: TxParams,
        block_identifier: Optional[BlockIdentifier] = None,
        state_override: Optional[CallOverride] = None,
    ) -> HexBytes:
        max_redirects = self.w3.provider.ccip_read_max_redirects

        if not max_redirects or max_redirects < 4:
            raise ValueError(
                "ccip_read_max_redirects property on provider must be at least 4."
            )

        for _ in range(max_redirects):
            try:
                return await self._call(transaction, block_identifier, state_override)
            except OffchainLookup as offchain_lookup:
                durin_calldata = await async_handle_offchain_lookup(
                    offchain_lookup.payload,
                    transaction,
                )
                transaction["data"] = durin_calldata

        raise TooManyRequests("Too many CCIP read redirects")

    # eth_createAccessList

    _create_access_list: Method[
        Callable[
            [TxParams, Optional[BlockIdentifier]],
            Awaitable[CreateAccessListResponse],
        ]
    ] = Method(RPC.eth_createAccessList, mungers=[BaseEth.create_access_list_munger])

    async def create_access_list(
        self,
        transaction: TxParams,
        block_identifier: Optional[BlockIdentifier] = None,
    ) -> CreateAccessListResponse:
        return await self._create_access_list(transaction, block_identifier)

    # eth_estimateGas

    _estimate_gas: Method[
        Callable[[TxParams, Optional[BlockIdentifier]], Awaitable[int]]
    ] = Method(RPC.eth_estimateGas, mungers=[BaseEth.estimate_gas_munger])

    async def estimate_gas(
        self, transaction: TxParams, block_identifier: Optional[BlockIdentifier] = None
    ) -> int:
        return await self._estimate_gas(transaction, block_identifier)

    # eth_getTransactionByHash

    _get_transaction: Method[Callable[[_Hash32], Awaitable[TxData]]] = Method(
        RPC.eth_getTransactionByHash, mungers=[default_root_munger]
    )

    async def get_transaction(self, transaction_hash: _Hash32) -> TxData:
        return await self._get_transaction(transaction_hash)

    # eth_getRawTransactionByHash

    _get_raw_transaction: Method[Callable[[_Hash32], Awaitable[HexBytes]]] = Method(
        RPC.eth_getRawTransactionByHash, mungers=[default_root_munger]
    )

    async def get_raw_transaction(self, transaction_hash: _Hash32) -> HexBytes:
        return await self._get_raw_transaction(transaction_hash)

    # eth_getTransactionByBlockNumberAndIndex
    # eth_getTransactionByBlockHashAndIndex

    _get_transaction_by_block: Method[
        Callable[[BlockIdentifier, int], Awaitable[TxData]]
    ] = Method(
        method_choice_depends_on_args=select_method_for_block_identifier(
            if_predefined=RPC.eth_getTransactionByBlockNumberAndIndex,
            if_hash=RPC.eth_getTransactionByBlockHashAndIndex,
            if_number=RPC.eth_getTransactionByBlockNumberAndIndex,
        ),
        mungers=[default_root_munger],
    )

    async def get_transaction_by_block(
        self, block_identifier: BlockIdentifier, index: int
    ) -> TxData:
        return await self._get_transaction_by_block(block_identifier, index)

    # eth_getRawTransactionByBlockHashAndIndex
    # eth_getRawTransactionByBlockNumberAndIndex

    _get_raw_transaction_by_block: Method[
        Callable[[BlockIdentifier, int], Awaitable[HexBytes]]
    ] = Method(
        method_choice_depends_on_args=select_method_for_block_identifier(
            if_predefined=RPC.eth_getRawTransactionByBlockNumberAndIndex,
            if_hash=RPC.eth_getRawTransactionByBlockHashAndIndex,
            if_number=RPC.eth_getRawTransactionByBlockNumberAndIndex,
        ),
        mungers=[default_root_munger],
    )

    async def get_raw_transaction_by_block(
        self, block_identifier: BlockIdentifier, index: int
    ) -> HexBytes:
        return await self._get_raw_transaction_by_block(block_identifier, index)

    # eth_getBlockTransactionCountByHash
    # eth_getBlockTransactionCountByNumber

    get_block_transaction_count: Method[Callable[[BlockIdentifier], Awaitable[int]]] = (
        Method(
            method_choice_depends_on_args=select_method_for_block_identifier(
                if_predefined=RPC.eth_getBlockTransactionCountByNumber,
                if_hash=RPC.eth_getBlockTransactionCountByHash,
                if_number=RPC.eth_getBlockTransactionCountByNumber,
            ),
            mungers=[default_root_munger],
        )
    )

    # eth_sendTransaction

    _send_transaction: Method[Callable[[TxParams], Awaitable[HexBytes]]] = Method(
        RPC.eth_sendTransaction, mungers=[BaseEth.send_transaction_munger]
    )

    async def send_transaction(self, transaction: TxParams) -> HexBytes:
        return await self._send_transaction(transaction)

    # eth_sendRawTransaction

    _send_raw_transaction: Method[
        Callable[[Union[HexStr, bytes]], Awaitable[HexBytes]]
    ] = Method(
        RPC.eth_sendRawTransaction,
        mungers=[default_root_munger],
    )

    async def send_raw_transaction(self, transaction: Union[HexStr, bytes]) -> HexBytes:
        return await self._send_raw_transaction(transaction)

    # eth_getBlockByHash
    # eth_getBlockByNumber

    _get_block: Method[Callable[[BlockIdentifier, bool], Awaitable[BlockData]]] = (
        Method(
            method_choice_depends_on_args=select_method_for_block_identifier(
                if_predefined=RPC.eth_getBlockByNumber,
                if_hash=RPC.eth_getBlockByHash,
                if_number=RPC.eth_getBlockByNumber,
            ),
            mungers=[BaseEth.get_block_munger],
        )
    )

    async def get_block(
        self, block_identifier: BlockIdentifier, full_transactions: bool = False
    ) -> BlockData:
        return await self._get_block(block_identifier, full_transactions)

    # eth_getBalance

    _get_balance: Method[
        Callable[
            [Union[Address, ChecksumAddress, ENS], Optional[BlockIdentifier]],
            Awaitable[Wei],
        ]
    ] = Method(
        RPC.eth_getBalance,
        mungers=[BaseEth.block_id_munger],
    )

    async def get_balance(
        self,
        account: Union[Address, ChecksumAddress, ENS],
        block_identifier: Optional[BlockIdentifier] = None,
    ) -> Wei:
        return await self._get_balance(account, block_identifier)

    # eth_getCode

    _get_code: Method[
        Callable[
            [Union[Address, ChecksumAddress, ENS], Optional[BlockIdentifier]],
            Awaitable[HexBytes],
        ]
    ] = Method(RPC.eth_getCode, mungers=[BaseEth.block_id_munger])

    async def get_code(
        self,
        account: Union[Address, ChecksumAddress, ENS],
        block_identifier: Optional[BlockIdentifier] = None,
    ) -> HexBytes:
        return await self._get_code(account, block_identifier)

    # eth_getLogs

    _get_logs: Method[Callable[[FilterParams], Awaitable[List[LogReceipt]]]] = Method(
        RPC.eth_getLogs, mungers=[default_root_munger]
    )

    async def get_logs(
        self,
        filter_params: FilterParams,
    ) -> List[LogReceipt]:
        return await self._get_logs(filter_params)

    # eth_getTransactionCount

    _get_transaction_count: Method[
        Callable[
            [Union[Address, ChecksumAddress, ENS], Optional[BlockIdentifier]],
            Awaitable[Nonce],
        ]
    ] = Method(
        RPC.eth_getTransactionCount,
        mungers=[BaseEth.block_id_munger],
    )

    async def get_transaction_count(
        self,
        account: Union[Address, ChecksumAddress, ENS],
        block_identifier: Optional[BlockIdentifier] = None,
    ) -> Nonce:
        return await self._get_transaction_count(account, block_identifier)

    # eth_getTransactionReceipt

    _transaction_receipt: Method[Callable[[_Hash32], Awaitable[TxReceipt]]] = Method(
        RPC.eth_getTransactionReceipt, mungers=[default_root_munger]
    )

    async def get_transaction_receipt(self, transaction_hash: _Hash32) -> TxReceipt:
        return await self._transaction_receipt(transaction_hash)

    async def wait_for_transaction_receipt(
        self, transaction_hash: _Hash32, timeout: float = 120, poll_latency: float = 0.1
    ) -> TxReceipt:
        async def _wait_for_tx_receipt_with_timeout(
            _tx_hash: _Hash32, _poll_latency: float
        ) -> TxReceipt:
            while True:
                try:
                    tx_receipt = await self._transaction_receipt(_tx_hash)
                except (TransactionNotFound, TransactionIndexingInProgress):
                    tx_receipt = None
                if tx_receipt is not None:
                    break
                await asyncio.sleep(poll_latency)
            return tx_receipt

        try:
            return await asyncio.wait_for(
                _wait_for_tx_receipt_with_timeout(transaction_hash, poll_latency),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            raise TimeExhausted(
                f"Transaction {HexBytes(transaction_hash) !r} is not in the chain "
                f"after {timeout} seconds"
            )

    # eth_getStorageAt

    _get_storage_at: Method[
        Callable[
            [Union[Address, ChecksumAddress, ENS], int, Optional[BlockIdentifier]],
            Awaitable[HexBytes],
        ]
    ] = Method(
        RPC.eth_getStorageAt,
        mungers=[BaseEth.get_storage_at_munger],
    )

    async def get_storage_at(
        self,
        account: Union[Address, ChecksumAddress, ENS],
        position: int,
        block_identifier: Optional[BlockIdentifier] = None,
    ) -> HexBytes:
        return await self._get_storage_at(account, position, block_identifier)

    async def replace_transaction(
        self, transaction_hash: _Hash32, new_transaction: TxParams
    ) -> HexBytes:
        current_transaction = await async_get_required_transaction(
            self.w3, transaction_hash
        )
        return await async_replace_transaction(
            self.w3, current_transaction, new_transaction
        )

    # todo: Update Any to stricter kwarg checking with TxParams
    # https://github.com/python/mypy/issues/4441
    async def modify_transaction(
        self, transaction_hash: _Hash32, **transaction_params: Any
    ) -> HexBytes:
        assert_valid_transaction_params(cast(TxParams, transaction_params))

        current_transaction = await async_get_required_transaction(
            self.w3, transaction_hash
        )
        current_transaction_params = extract_valid_transaction_params(
            current_transaction
        )
        new_transaction = merge(current_transaction_params, transaction_params)

        return await async_replace_transaction(
            self.w3, current_transaction, new_transaction
        )

    # eth_sign

    _sign: Method[Callable[..., Awaitable[HexStr]]] = Method(
        RPC.eth_sign, mungers=[BaseEth.sign_munger]
    )

    async def sign(
        self,
        account: Union[Address, ChecksumAddress, ENS],
        data: Union[int, bytes] = None,
        hexstr: HexStr = None,
        text: str = None,
    ) -> HexStr:
        return await self._sign(account, data, hexstr, text)

    # eth_signTransaction

    _sign_transaction: Method[Callable[[TxParams], Awaitable[SignedTx]]] = Method(
        RPC.eth_signTransaction,
        mungers=[default_root_munger],
    )

    async def sign_transaction(self, transaction: TxParams) -> SignedTx:
        return await self._sign_transaction(transaction)

    # eth_signTypedData

    _sign_typed_data: Method[
        Callable[[Union[Address, ChecksumAddress, ENS], str], Awaitable[HexStr]]
    ] = Method(
        RPC.eth_signTypedData,
        mungers=[default_root_munger],
    )

    async def sign_typed_data(
        self, account: Union[Address, ChecksumAddress, ENS], data: str
    ) -> HexStr:
        return await self._sign_typed_data(account, data)

    # eth_getUncleCountByBlockHash
    # eth_getUncleCountByBlockNumber

    _get_uncle_count: Method[Callable[[BlockIdentifier], Awaitable[int]]] = Method(
        method_choice_depends_on_args=select_method_for_block_identifier(
            if_predefined=RPC.eth_getUncleCountByBlockNumber,
            if_hash=RPC.eth_getUncleCountByBlockHash,
            if_number=RPC.eth_getUncleCountByBlockNumber,
        ),
        mungers=[default_root_munger],
    )

    async def get_uncle_count(self, block_identifier: BlockIdentifier) -> int:
        return await self._get_uncle_count(block_identifier)

    # eth_newFilter, eth_newBlockFilter, eth_newPendingTransactionFilter

    filter: Method[
        Callable[[Optional[Union[str, FilterParams, HexStr]]], Awaitable[AsyncFilter]]
    ] = Method(
        method_choice_depends_on_args=select_filter_method(
            if_new_block_filter=RPC.eth_newBlockFilter,
            if_new_pending_transaction_filter=RPC.eth_newPendingTransactionFilter,
            if_new_filter=RPC.eth_newFilter,
        ),
        mungers=[BaseEth.filter_munger],
    )

    # eth_getFilterChanges, eth_getFilterLogs, eth_uninstallFilter

    _get_filter_changes: Method[Callable[[HexStr], Awaitable[List[LogReceipt]]]] = (
        Method(RPC.eth_getFilterChanges, mungers=[default_root_munger])
    )

    async def get_filter_changes(self, filter_id: HexStr) -> List[LogReceipt]:
        return await self._get_filter_changes(filter_id)

    _get_filter_logs: Method[Callable[[HexStr], Awaitable[List[LogReceipt]]]] = Method(
        RPC.eth_getFilterLogs, mungers=[default_root_munger]
    )

    async def get_filter_logs(self, filter_id: HexStr) -> List[LogReceipt]:
        return await self._get_filter_logs(filter_id)

    _uninstall_filter: Method[Callable[[HexStr], Awaitable[bool]]] = Method(
        RPC.eth_uninstallFilter,
        mungers=[default_root_munger],
    )

    async def uninstall_filter(self, filter_id: HexStr) -> bool:
        return await self._uninstall_filter(filter_id)

    # eth_subscribe / eth_unsubscribe

    _subscribe: Method[Callable[[SubscriptionType], Awaitable[HexStr]]] = Method(
        RPC.eth_subscribe,
        mungers=[default_root_munger],
    )

    _subscribe_with_args: Method[
        Callable[
            [
                SubscriptionType,
                Optional[Union[LogsSubscriptionArg, bool]],
            ],
            Awaitable[HexStr],
        ]
    ] = Method(
        RPC.eth_subscribe,
        mungers=[default_root_munger],
    )

    async def subscribe(
        self,
        subscription_type: SubscriptionType,
        subscription_arg: Optional[
            Union[
                LogsSubscriptionArg,  # logs, optional filter params
                bool,  # newPendingTransactions, full_transactions
            ]
        ] = None,
    ) -> HexStr:
        if not isinstance(self.w3.provider, PersistentConnectionProvider):
            raise MethodUnavailable(
                "eth_subscribe is only supported with providers that support "
                "persistent connections."
            )

        if subscription_arg is None:
            return await self._subscribe(subscription_type)

        return await self._subscribe_with_args(subscription_type, subscription_arg)

    _unsubscribe: Method[Callable[[HexStr], Awaitable[bool]]] = Method(
        RPC.eth_unsubscribe,
        mungers=[default_root_munger],
    )

    async def unsubscribe(self, subscription_id: HexStr) -> bool:
        if not isinstance(self.w3.provider, PersistentConnectionProvider):
            raise MethodUnavailable(
                "eth_unsubscribe is only supported with providers that support "
                "persistent connections."
            )

        return await self._unsubscribe(subscription_id)

    # -- contract methods -- #

    @overload
    def contract(self, address: None = None, **kwargs: Any) -> Type[AsyncContract]: ...

    @overload
    def contract(
        self, address: Union[Address, ChecksumAddress, ENS], **kwargs: Any
    ) -> AsyncContract: ...

    def contract(
        self,
        address: Optional[Union[Address, ChecksumAddress, ENS]] = None,
        **kwargs: Any,
    ) -> Union[Type[AsyncContract], AsyncContract]:
        ContractFactoryClass = kwargs.pop(
            "ContractFactoryClass", self._default_contract_factory
        )

        ContractFactory = ContractFactoryClass.factory(self.w3, **kwargs)

        if address:
            return ContractFactory(address)
        else:
            return ContractFactory

    def set_contract_factory(
        self,
        contract_factory: Type[Union[AsyncContract, AsyncContractCaller]],
    ) -> None:
        self._default_contract_factory = contract_factory

    def contract(self, address: None = None, **kwargs: Any) -> Type[AsyncContract]: ...

    def contract(
        self, address: Union[Address, ChecksumAddress, ENS], **kwargs: Any
    ) -> AsyncContract: ...

    def contract(
        self,
        address: Optional[Union[Address, ChecksumAddress, ENS]] = None,
        **kwargs: Any,
    ) -> Union[Type[AsyncContract], AsyncContract]:
        ContractFactoryClass = kwargs.pop(
            "ContractFactoryClass", self._default_contract_factory
        )

        ContractFactory = ContractFactoryClass.factory(self.w3, **kwargs)

        if address:
            return ContractFactory(address)
        else:
            return ContractFactory

    def set_contract_factory(
        self,
        contract_factory: Type[Union[AsyncContract, AsyncContractCaller]],
    ) -> None:
        self._default_contract_factory = contract_factory
# --- Merged from async_base.py ---

class AsyncBaseProvider:
    _middlewares: Tuple[AsyncMiddleware, ...] = ()
    # a tuple of (all_middlewares, request_func)
    _request_func_cache: Tuple[
        Tuple[AsyncMiddleware, ...], Callable[..., Coroutine[Any, Any, RPCResponse]]
    ] = (
        None,
        None,
    )

    is_async = True
    has_persistent_connection = False
    global_ccip_read_enabled: bool = True
    ccip_read_max_redirects: int = 4

    @property
    def middlewares(self) -> Tuple[AsyncMiddleware, ...]:
        return self._middlewares

    @middlewares.setter
    def middlewares(self, values: MiddlewareOnion) -> None:
        # tuple(values) converts to MiddlewareOnion -> Tuple[Middleware, ...]
        self._middlewares = tuple(values)  # type: ignore

    async def request_func(
        self, async_w3: "AsyncWeb3", outer_middlewares: AsyncMiddlewareOnion
    ) -> Callable[..., Coroutine[Any, Any, RPCResponse]]:
        # type ignored b/c tuple(MiddlewareOnion) converts to tuple of middlewares
        all_middlewares: Tuple[AsyncMiddleware] = tuple(outer_middlewares) + tuple(self.middlewares)  # type: ignore  # noqa: E501

        cache_key = self._request_func_cache[0]
        if cache_key is None or cache_key != all_middlewares:
            self._request_func_cache = (
                all_middlewares,
                await self._generate_request_func(async_w3, all_middlewares),
            )
        return self._request_func_cache[-1]

    async def _generate_request_func(
        self, async_w3: "AsyncWeb3", middlewares: Sequence[AsyncMiddleware]
    ) -> Callable[..., Coroutine[Any, Any, RPCResponse]]:
        return await async_combine_middlewares(
            middlewares=middlewares,
            async_w3=async_w3,
            provider_request_fn=self.make_request,
        )

    async def make_request(self, method: RPCEndpoint, params: Any) -> RPCResponse:
        raise NotImplementedError("Providers must implement this method")

    async def is_connected(self, show_traceback: bool = False) -> bool:
        raise NotImplementedError("Providers must implement this method")

class AsyncJSONBaseProvider(AsyncBaseProvider):
    def __init__(self) -> None:
        super().__init__()
        self.request_counter = itertools.count()

    def encode_rpc_request(self, method: RPCEndpoint, params: Any) -> bytes:
        request_id = next(self.request_counter)
        rpc_dict = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": request_id,
        }
        encoded = FriendlyJsonSerde().json_encode(rpc_dict, cls=Web3JsonEncoder)
        return to_bytes(text=encoded)

    def decode_rpc_response(self, raw_response: bytes) -> RPCResponse:
        text_response = str(
            to_text(raw_response) if not is_text(raw_response) else raw_response
        )
        return cast(RPCResponse, FriendlyJsonSerde().json_decode(text_response))

    async def is_connected(self, show_traceback: bool = False) -> bool:
        try:
            response = await self.make_request(RPCEndpoint("web3_clientVersion"), [])
        except OSError as e:
            if show_traceback:
                raise ProviderConnectionError(
                    f"Problem connecting to provider with error: {type(e)}: {e}"
                )
            return False

        if "error" in response:
            if show_traceback:
                raise ProviderConnectionError(
                    f"Error received from provider: {response}"
                )
            return False

        if response["jsonrpc"] == "2.0":
            return True
        else:
            if show_traceback:
                raise ProviderConnectionError(f"Bad jsonrpc version: {response}")
            return False

    def middlewares(self) -> Tuple[AsyncMiddleware, ...]:
        return self._middlewares

    def middlewares(self, values: MiddlewareOnion) -> None:
        # tuple(values) converts to MiddlewareOnion -> Tuple[Middleware, ...]
        self._middlewares = tuple(values)  # type: ignore

    def encode_rpc_request(self, method: RPCEndpoint, params: Any) -> bytes:
        request_id = next(self.request_counter)
        rpc_dict = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": request_id,
        }
        encoded = FriendlyJsonSerde().json_encode(rpc_dict, cls=Web3JsonEncoder)
        return to_bytes(text=encoded)

    def decode_rpc_response(self, raw_response: bytes) -> RPCResponse:
        text_response = str(
            to_text(raw_response) if not is_text(raw_response) else raw_response
        )
        return cast(RPCResponse, FriendlyJsonSerde().json_decode(text_response))
# --- Merged from async_rpc.py ---

class AsyncHTTPProvider(AsyncJSONBaseProvider):
    logger = logging.getLogger("web3.providers.AsyncHTTPProvider")
    endpoint_uri = None
    _request_kwargs = None
    # type ignored b/c conflict with _middlewares attr on AsyncBaseProvider
    _middlewares: Tuple[AsyncMiddleware, ...] = NamedElementOnion([(async_http_retry_request_middleware, "http_retry_request")])  # type: ignore # noqa: E501

    def __init__(
        self,
        endpoint_uri: Optional[Union[URI, str]] = None,
        request_kwargs: Optional[Any] = None,
    ) -> None:
        if endpoint_uri is None:
            self.endpoint_uri = get_default_http_endpoint()
        else:
            self.endpoint_uri = URI(endpoint_uri)

        self._request_kwargs = request_kwargs or {}

        super().__init__()

    async def cache_async_session(self, session: ClientSession) -> ClientSession:
        return await _async_cache_and_return_session(self.endpoint_uri, session)

    def __str__(self) -> str:
        return f"RPC connection {self.endpoint_uri}"

    @to_dict
    def get_request_kwargs(self) -> Iterable[Tuple[str, Any]]:
        if "headers" not in self._request_kwargs:
            yield "headers", self.get_request_headers()
        for key, value in self._request_kwargs.items():
            yield key, value

    def get_request_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "User-Agent": construct_user_agent(str(type(self))),
        }

    async def make_request(self, method: RPCEndpoint, params: Any) -> RPCResponse:
        self.logger.debug(
            f"Making request HTTP. URI: {self.endpoint_uri}, Method: {method}"
        )
        request_data = self.encode_rpc_request(method, params)
        raw_response = await async_make_post_request(
            self.endpoint_uri, request_data, **self.get_request_kwargs()
        )
        response = self.decode_rpc_response(raw_response)
        self.logger.debug(
            f"Getting response HTTP. URI: {self.endpoint_uri}, "
            f"Method: {method}, Response: {response}"
        )
        return response

    def __str__(self) -> str:
        return f"RPC connection {self.endpoint_uri}"

    def get_request_kwargs(self) -> Iterable[Tuple[str, Any]]:
        if "headers" not in self._request_kwargs:
            yield "headers", self.get_request_headers()
        for key, value in self._request_kwargs.items():
            yield key, value

    def get_request_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "User-Agent": construct_user_agent(str(type(self))),
        }
# --- Merged from async_utils.py ---

class _IteratorToAsyncIterator(t.Generic[V]):
    def __init__(self, iterator: "t.Iterator[V]"):
        self._iterator = iterator

    def __aiter__(self) -> "te.Self":
        return self

    async def __anext__(self) -> V:
        try:
            return next(self._iterator)
        except StopIteration as e:
            raise StopAsyncIteration(e.value) from e

def auto_aiter(
    iterable: "t.Union[t.AsyncIterable[V], t.Iterable[V]]",
) -> "t.AsyncIterator[V]":
    if hasattr(iterable, "__aiter__"):
        return iterable.__aiter__()
    else:
        return _IteratorToAsyncIterator(iter(iterable))

    def __aiter__(self) -> "te.Self":
        return self
# --- Merged from synchronize.py ---

class SemLock:

    _rand = tempfile._RandomNameSequence()

    def __init__(self, kind, value, maxvalue, name=None):
        # unlink_now is only used on win32 or when we are using fork.
        unlink_now = False
        if name is None:
            # Try to find an unused name for the SemLock instance.
            for _ in range(100):
                try:
                    self._semlock = _SemLock(
                        kind, value, maxvalue, SemLock._make_name(), unlink_now
                    )
                except FileExistsError:  # pragma: no cover
                    pass
                else:
                    break
            else:  # pragma: no cover
                raise FileExistsError("cannot find name for semaphore")
        else:
            self._semlock = _SemLock(kind, value, maxvalue, name, unlink_now)
        self.name = name
        util.debug(
            f"created semlock with handle {self._semlock.handle} and name "
            f'"{self.name}"'
        )

        self._make_methods()

        def _after_fork(obj):
            obj._semlock._after_fork()

        util.register_after_fork(self, _after_fork)

        # When the object is garbage collected or the
        # process shuts down we unlink the semaphore name
        resource_tracker.register(self._semlock.name, "semlock")
        util.Finalize(
            self, SemLock._cleanup, (self._semlock.name,), exitpriority=0
        )

    @staticmethod
    def _cleanup(name):
        try:
            sem_unlink(name)
        except FileNotFoundError:
            # Already unlinked, possibly by user code: ignore and make sure to
            # unregister the semaphore from the resource tracker.
            pass
        finally:
            resource_tracker.unregister(name, "semlock")

    def _make_methods(self):
        self.acquire = self._semlock.acquire
        self.release = self._semlock.release

    def __enter__(self):
        return self._semlock.acquire()

    def __exit__(self, *args):
        return self._semlock.release()

    def __getstate__(self):
        assert_spawning(self)
        sl = self._semlock
        h = sl.handle
        return (h, sl.kind, sl.maxvalue, sl.name)

    def __setstate__(self, state):
        self._semlock = _SemLock._rebuild(*state)
        util.debug(
            f'recreated blocker with handle {state[0]!r} and name "{state[3]}"'
        )
        self._make_methods()

    @staticmethod
    def _make_name():
        # OSX does not support long names for semaphores
        return f"/loky-{os.getpid()}-{next(SemLock._rand)}"

class Semaphore(SemLock):
    def __init__(self, value=1):
        SemLock.__init__(self, SEMAPHORE, value, SEM_VALUE_MAX)

    def get_value(self):
        if sys.platform == "darwin":
            raise NotImplementedError("OSX does not implement sem_getvalue")
        return self._semlock._get_value()

    def __repr__(self):
        try:
            value = self._semlock._get_value()
        except Exception:
            value = "unknown"
        return f"<{self.__class__.__name__}(value={value})>"

class BoundedSemaphore(Semaphore):
    def __init__(self, value=1):
        SemLock.__init__(self, SEMAPHORE, value, value)

    def __repr__(self):
        try:
            value = self._semlock._get_value()
        except Exception:
            value = "unknown"
        return (
            f"<{self.__class__.__name__}(value={value}, "
            f"maxvalue={self._semlock.maxvalue})>"
        )

class Lock(SemLock):
    def __init__(self):
        super().__init__(SEMAPHORE, 1, 1)

    def __repr__(self):
        try:
            if self._semlock._is_mine():
                name = process.current_process().name
                if threading.current_thread().name != "MainThread":
                    name = f"{name}|{threading.current_thread().name}"
            elif self._semlock._get_value() == 1:
                name = "None"
            elif self._semlock._count() > 0:
                name = "SomeOtherThread"
            else:
                name = "SomeOtherProcess"
        except Exception:
            name = "unknown"
        return f"<{self.__class__.__name__}(owner={name})>"

class RLock(SemLock):
    def __init__(self):
        super().__init__(RECURSIVE_MUTEX, 1, 1)

    def __repr__(self):
        try:
            if self._semlock._is_mine():
                name = process.current_process().name
                if threading.current_thread().name != "MainThread":
                    name = f"{name}|{threading.current_thread().name}"
                count = self._semlock._count()
            elif self._semlock._get_value() == 1:
                name, count = "None", 0
            elif self._semlock._count() > 0:
                name, count = "SomeOtherThread", "nonzero"
            else:
                name, count = "SomeOtherProcess", "nonzero"
        except Exception:
            name, count = "unknown", "unknown"
        return f"<{self.__class__.__name__}({name}, {count})>"

class Condition:
    def __init__(self, lock=None):
        self._lock = lock or RLock()
        self._sleeping_count = Semaphore(0)
        self._woken_count = Semaphore(0)
        self._wait_semaphore = Semaphore(0)
        self._make_methods()

    def __getstate__(self):
        assert_spawning(self)
        return (
            self._lock,
            self._sleeping_count,
            self._woken_count,
            self._wait_semaphore,
        )

    def __setstate__(self, state):
        (
            self._lock,
            self._sleeping_count,
            self._woken_count,
            self._wait_semaphore,
        ) = state
        self._make_methods()

    def __enter__(self):
        return self._lock.__enter__()

    def __exit__(self, *args):
        return self._lock.__exit__(*args)

    def _make_methods(self):
        self.acquire = self._lock.acquire
        self.release = self._lock.release

    def __repr__(self):
        try:
            num_waiters = (
                self._sleeping_count._semlock._get_value()
                - self._woken_count._semlock._get_value()
            )
        except Exception:
            num_waiters = "unknown"
        return f"<{self.__class__.__name__}({self._lock}, {num_waiters})>"

    def wait(self, timeout=None):
        assert (
            self._lock._semlock._is_mine()
        ), "must acquire() condition before using wait()"

        # indicate that this thread is going to sleep
        self._sleeping_count.release()

        # release lock
        count = self._lock._semlock._count()
        for _ in range(count):
            self._lock.release()

        try:
            # wait for notification or timeout
            return self._wait_semaphore.acquire(True, timeout)
        finally:
            # indicate that this thread has woken
            self._woken_count.release()

            # reacquire lock
            for _ in range(count):
                self._lock.acquire()

    def notify(self):
        assert self._lock._semlock._is_mine(), "lock is not owned"
        assert not self._wait_semaphore.acquire(False)

        # to take account of timeouts since last notify() we subtract
        # woken_count from sleeping_count and rezero woken_count
        while self._woken_count.acquire(False):
            res = self._sleeping_count.acquire(False)
            assert res

        if self._sleeping_count.acquire(False):  # try grabbing a sleeper
            self._wait_semaphore.release()  # wake up one sleeper
            self._woken_count.acquire()  # wait for the sleeper to wake

            # rezero _wait_semaphore in case a timeout just happened
            self._wait_semaphore.acquire(False)

    def notify_all(self):
        assert self._lock._semlock._is_mine(), "lock is not owned"
        assert not self._wait_semaphore.acquire(False)

        # to take account of timeouts since last notify*() we subtract
        # woken_count from sleeping_count and rezero woken_count
        while self._woken_count.acquire(False):
            res = self._sleeping_count.acquire(False)
            assert res

        sleepers = 0
        while self._sleeping_count.acquire(False):
            self._wait_semaphore.release()  # wake up one sleeper
            sleepers += 1

        if sleepers:
            for _ in range(sleepers):
                self._woken_count.acquire()  # wait for a sleeper to wake

            # rezero wait_semaphore in case some timeouts just happened
            while self._wait_semaphore.acquire(False):
                pass

    def wait_for(self, predicate, timeout=None):
        result = predicate()
        if result:
            return result
        if timeout is not None:
            endtime = _time() + timeout
        else:
            endtime = None
            waittime = None
        while not result:
            if endtime is not None:
                waittime = endtime - _time()
                if waittime <= 0:
                    break
            self.wait(waittime)
            result = predicate()
        return result

class Event:
    def __init__(self):
        self._cond = Condition(Lock())
        self._flag = Semaphore(0)

    def is_set(self):
        with self._cond:
            if self._flag.acquire(False):
                self._flag.release()
                return True
            return False

    def set(self):
        with self._cond:
            self._flag.acquire(False)
            self._flag.release()
            self._cond.notify_all()

    def clear(self):
        with self._cond:
            self._flag.acquire(False)

    def wait(self, timeout=None):
        with self._cond:
            if self._flag.acquire(False):
                self._flag.release()
            else:
                self._cond.wait(timeout)

            if self._flag.acquire(False):
                self._flag.release()
                return True
            return False

    def _cleanup(name):
        try:
            sem_unlink(name)
        except FileNotFoundError:
            # Already unlinked, possibly by user code: ignore and make sure to
            # unregister the semaphore from the resource tracker.
            pass
        finally:
            resource_tracker.unregister(name, "semlock")

    def _make_methods(self):
        self.acquire = self._semlock.acquire
        self.release = self._semlock.release

    def __getstate__(self):
        assert_spawning(self)
        sl = self._semlock
        h = sl.handle
        return (h, sl.kind, sl.maxvalue, sl.name)

    def __setstate__(self, state):
        self._semlock = _SemLock._rebuild(*state)
        util.debug(
            f'recreated blocker with handle {state[0]!r} and name "{state[3]}"'
        )
        self._make_methods()

    def _make_name():
        # OSX does not support long names for semaphores
        return f"/loky-{os.getpid()}-{next(SemLock._rand)}"

    def get_value(self):
        if sys.platform == "darwin":
            raise NotImplementedError("OSX does not implement sem_getvalue")
        return self._semlock._get_value()

    def __repr__(self):
        try:
            value = self._semlock._get_value()
        except Exception:
            value = "unknown"
        return f"<{self.__class__.__name__}(value={value})>"

    def __repr__(self):
        try:
            value = self._semlock._get_value()
        except Exception:
            value = "unknown"
        return (
            f"<{self.__class__.__name__}(value={value}, "
            f"maxvalue={self._semlock.maxvalue})>"
        )

    def __repr__(self):
        try:
            if self._semlock._is_mine():
                name = process.current_process().name
                if threading.current_thread().name != "MainThread":
                    name = f"{name}|{threading.current_thread().name}"
            elif self._semlock._get_value() == 1:
                name = "None"
            elif self._semlock._count() > 0:
                name = "SomeOtherThread"
            else:
                name = "SomeOtherProcess"
        except Exception:
            name = "unknown"
        return f"<{self.__class__.__name__}(owner={name})>"

    def __repr__(self):
        try:
            if self._semlock._is_mine():
                name = process.current_process().name
                if threading.current_thread().name != "MainThread":
                    name = f"{name}|{threading.current_thread().name}"
                count = self._semlock._count()
            elif self._semlock._get_value() == 1:
                name, count = "None", 0
            elif self._semlock._count() > 0:
                name, count = "SomeOtherThread", "nonzero"
            else:
                name, count = "SomeOtherProcess", "nonzero"
        except Exception:
            name, count = "unknown", "unknown"
        return f"<{self.__class__.__name__}({name}, {count})>"

    def __getstate__(self):
        assert_spawning(self)
        return (
            self._lock,
            self._sleeping_count,
            self._woken_count,
            self._wait_semaphore,
        )

    def __setstate__(self, state):
        (
            self._lock,
            self._sleeping_count,
            self._woken_count,
            self._wait_semaphore,
        ) = state
        self._make_methods()

    def _make_methods(self):
        self.acquire = self._lock.acquire
        self.release = self._lock.release

    def __repr__(self):
        try:
            num_waiters = (
                self._sleeping_count._semlock._get_value()
                - self._woken_count._semlock._get_value()
            )
        except Exception:
            num_waiters = "unknown"
        return f"<{self.__class__.__name__}({self._lock}, {num_waiters})>"

    def wait(self, timeout=None):
        assert (
            self._lock._semlock._is_mine()
        ), "must acquire() condition before using wait()"

        # indicate that this thread is going to sleep
        self._sleeping_count.release()

        # release lock
        count = self._lock._semlock._count()
        for _ in range(count):
            self._lock.release()

        try:
            # wait for notification or timeout
            return self._wait_semaphore.acquire(True, timeout)
        finally:
            # indicate that this thread has woken
            self._woken_count.release()

            # reacquire lock
            for _ in range(count):
                self._lock.acquire()

    def notify(self):
        assert self._lock._semlock._is_mine(), "lock is not owned"
        assert not self._wait_semaphore.acquire(False)

        # to take account of timeouts since last notify() we subtract
        # woken_count from sleeping_count and rezero woken_count
        while self._woken_count.acquire(False):
            res = self._sleeping_count.acquire(False)
            assert res

        if self._sleeping_count.acquire(False):  # try grabbing a sleeper
            self._wait_semaphore.release()  # wake up one sleeper
            self._woken_count.acquire()  # wait for the sleeper to wake

            # rezero _wait_semaphore in case a timeout just happened
            self._wait_semaphore.acquire(False)

    def notify_all(self):
        assert self._lock._semlock._is_mine(), "lock is not owned"
        assert not self._wait_semaphore.acquire(False)

        # to take account of timeouts since last notify*() we subtract
        # woken_count from sleeping_count and rezero woken_count
        while self._woken_count.acquire(False):
            res = self._sleeping_count.acquire(False)
            assert res

        sleepers = 0
        while self._sleeping_count.acquire(False):
            self._wait_semaphore.release()  # wake up one sleeper
            sleepers += 1

        if sleepers:
            for _ in range(sleepers):
                self._woken_count.acquire()  # wait for a sleeper to wake

            # rezero wait_semaphore in case some timeouts just happened
            while self._wait_semaphore.acquire(False):
                pass

    def wait_for(self, predicate, timeout=None):
        result = predicate()
        if result:
            return result
        if timeout is not None:
            endtime = _time() + timeout
        else:
            endtime = None
            waittime = None
        while not result:
            if endtime is not None:
                waittime = endtime - _time()
                if waittime <= 0:
                    break
            self.wait(waittime)
            result = predicate()
        return result

    def is_set(self):
        with self._cond:
            if self._flag.acquire(False):
                self._flag.release()
                return True
            return False

    def set(self):
        with self._cond:
            self._flag.acquire(False)
            self._flag.release()
            self._cond.notify_all()

    def clear(self):
        with self._cond:
            self._flag.acquire(False)

    def wait(self, timeout=None):
        with self._cond:
            if self._flag.acquire(False):
                self._flag.release()
            else:
                self._cond.wait(timeout)

            if self._flag.acquire(False):
                self._flag.release()
                return True
            return False

        def _after_fork(obj):
            obj._semlock._after_fork()
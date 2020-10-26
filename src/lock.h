/*
This file is a part of the NV Speech Player project. 
URL: https://bitbucket.org/nvaccess/speechplayer
Copyright 2014 NV Access Limited.
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2.0, as published by
the Free Software Foundation.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
This license can be found at:
http://www.gnu.org/licenses/old-licenses/gpl-2.0.html
*/

#ifndef NVDAHELPER_LOCK_H
#define NVDAHELPER_LOCK_H

#include <cassert>

#ifdef WIN32
	#include <windows.h>
#endif

/**
 * A class that provides a locking mechonism on objects.
 * The lock is reeentrant for the same thread.
 */
class LockableObject {
	private:
	#ifdef WIN32
		CRITICAL_SECTION _cs;
	#endif

	public:

	LockableObject() {
		#ifdef WIN32
			InitializeCriticalSection(&_cs);
		#endif
	}

	virtual ~LockableObject() {
		#ifdef WIN32
			DeleteCriticalSection(&_cs);
		#endif
	}

/**
 * Acquires access (possibly waighting until its free).
 */
	void acquire() {
		#ifdef WIN32
			EnterCriticalSection(&_cs);
	#endif
	}

/**
 * Releases exclusive access of the object.
 */
	void release() {
		#ifdef WIN32
			LeaveCriticalSection(&_cs);
		#endif
	}

};

/**
 * A class providing both exclusive locking, and reference counting with auto-deletion.
 * Do not use this in multiple inheritence.
 */
class LockableAutoFreeObject: private LockableObject {
	private:
	volatile long _refCount;

	protected:

long incRef() {
		#ifdef WIN32
			return InterlockedIncrement(&_refCount);
		#else
			return ++_refCount;
		#endif
	}

	long decRef() {
		#ifdef WIN32
			long refCount=InterlockedDecrement(&_refCount);
		#else
			long refCount=--_refCount;
		#endif

		if(refCount==0) {
			delete this;
		}
		assert(refCount>=0);
		return refCount;
	}

	public:

	LockableAutoFreeObject(): _refCount(1) {
	}

/**
 * Increases the reference count and acquires exclusive access.
 */
	void acquire() {
		incRef();
		LockableObject::acquire();
	}

	void release() {
		LockableObject::release();
		decRef();
	}

/**
 * Deletes this object if no one has acquired it, or indicates that it should be deleted once it has been released.
 */
	void requestDelete() {
		decRef();
	}

};

#endif
